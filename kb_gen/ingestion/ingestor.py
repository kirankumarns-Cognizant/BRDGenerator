"""
DocumentIngestor — walks service folders, enriches metadata, registers documents.

Ingestion flow per document:
1. Walk KB/<service>/ for matching file extensions.
2. Compute SHA256 hash for change detection.
3. If already embedded and hash unchanged: skip.
4. Read file content.
5. Call LLM to enrich metadata (description, tags, useful_for, entity_mentions).
6. If BRD: chunk with BRDChunker.
7. Embed chunks/document with vector_store.
8. Register metadata in DocumentRegistry.
9. Add node to DocumentHypergraph.
"""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from kb_gen.utils.artifact_id import generate_artifact_id
from kb_gen.utils.api_client import get_anthropic_client, sanitize_error
from kb_gen.ingestion.brd_chunker import BRDChunker
from kb_gen.hypergraph.placement_agent import PlacementAgent
from kb_gen.ingestion.artifact_renamer import ArtifactRenamer

_JSON_EXT = ".json"

SUPPORTED_EXTENSIONS = {".md", _JSON_EXT, ".txt", ".docx"}

ENRICH_SYSTEM = """You extract structured metadata from knowledge base documents.
Respond ONLY in valid JSON. No preamble. No markdown fences."""

ENRICH_PROMPT = """Extract metadata from this document.

Artifact type: {artifact_type}
Filename: {filename}
Service/Repo: {service}

Content (first 2000 chars):
{content}

Respond with ONLY this JSON (use empty string "" for any field you cannot determine):
{{
  "description": "one sentence describing what this document contains",
  "tags": ["relevant", "business", "tags"],
  "useful_for": ["test_case_writing", "code_generation", "requirement_clarification"],
  "entity_mentions": ["BusinessEntity1", "BusinessEntity2"],
  "brand": "one of ST|TW|TF|WFM|SHARED|EXT|VALUE or empty string",
  "domain": "business domain e.g. service_ordering|payments|identity|catalog|provisioning or empty",
  "feature": "specific feature within domain e.g. Activation|PortIn|Subscription or empty",
  "producer_agent": "one of brd_agent|qa_agent|coding_agent|human or empty",
  "confidence": "one of HIGH|MEDIUM|LOW"
}}"""


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def _build_canonical_name(
    brand: str, domain: str, feature: str, artifact_type: str, ext: str
) -> str:
    """Return naming-convention canonical name, e.g. ST_service_ordering_Activation_brd_v1.json.
    Any empty component is replaced with 'UNKNOWN' so the name is always parseable."""
    parts = [
        (brand or "UNKNOWN").upper(),
        (domain or "UNKNOWN").lower().replace(" ", "_"),
        (feature or "UNKNOWN").replace(" ", "_"),
        (artifact_type or "document").lower(),
        "v1",
    ]
    return "_".join(parts) + (f".{ext}" if ext else _JSON_EXT)


def _read_file(file_path: Path) -> str:
    """Read file content as text, handling encoding issues."""
    if file_path.suffix == ".json":
        try:
            with open(file_path) as f:
                data = json.load(f)
            return json.dumps(data, indent=2)
        except Exception:
            pass
    try:
        return file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


class DocumentIngestor:

    def __init__(
        self,
        registry,
        hypergraph,
        kb_root: str = "KB",
        model: str = "claude-haiku-4-5-20251001",
        vector_store=None,
        brd_chunking_enabled: bool = True,
        json_ingestion_enabled: bool = True,
        json_included_files: Optional[List[str]] = None,
    ):
        self.registry = registry
        self.hypergraph = hypergraph
        self.kb_root = Path(kb_root)
        self.model = model
        self.vector_store = vector_store
        self.brd_chunking_enabled = brd_chunking_enabled
        self.json_ingestion_enabled = json_ingestion_enabled
        self.json_included_files = set(json_included_files or [])
        self._chunker = BRDChunker() if brd_chunking_enabled else None
        self._placement_agent = PlacementAgent()
        self._renamer = ArtifactRenamer(kb_root=kb_root)
        self._client = None
        self._progress: Dict = {}
        self._progress_path = Path("logs/ingestion_progress.json")
        self._progress_path.parent.mkdir(parents=True, exist_ok=True)
        self._load_progress()

    def _get_client(self):
        if self._client is None:
            self._client = get_anthropic_client()
        return self._client

    # ── Progress checkpointing ───────────────────────────────────────────────────

    def _load_progress(self):
        if self._progress_path.exists():
            try:
                with open(self._progress_path) as f:
                    self._progress = json.load(f)
            except Exception:
                self._progress = {}

    def _save_progress(self):
        tmp = self._progress_path.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(self._progress, f, indent=2)
        import shutil
        shutil.move(str(tmp), str(self._progress_path))

    # ── Public API ───────────────────────────────────────────────────────────────

    def ingest_service(self, service_name: str) -> Dict:
        """Ingest all documents in KB/<service_name>/. Returns summary dict."""
        service_dir = self.kb_root / service_name
        if not service_dir.exists():
            print(f"[WARN] Service directory not found: {service_dir}")
            return {"service": service_name, "ingested": 0, "skipped": 0, "errors": 0}

        files = [
            f for f in service_dir.rglob("*")
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        ]

        ingested = skipped = errors = 0
        for file_path in files:
            try:
                result = self.ingest_file(file_path, service_name)
                if result == "skipped":
                    skipped += 1
                else:
                    ingested += 1
            except Exception as exc:
                import traceback
                errors += 1
                print(f"[ERROR] ingesting {file_path.name}: {sanitize_error(str(exc))}")
                traceback.print_exc()

        print(f"[OK] Service '{service_name}': {ingested} ingested, {skipped} skipped, {errors} errors")
        return {"service": service_name, "ingested": ingested, "skipped": skipped, "errors": errors}

    def ingest_file(self, file_path: Path, service: str = "") -> str:
        """
        Ingest a single file. Returns 'ingested' or 'skipped'.
        """
        if file_path.suffix.lower() == ".json":
            if not self.json_ingestion_enabled:
                return "skipped"
            if self.json_included_files and file_path.name not in self.json_included_files:
                return "skipped"

        content = _read_file(file_path)
        if not content.strip():
            return "skipped"

        file_hash = _sha256(content)
        progress_key = str(file_path)

        # Change detection
        if (
            self.vector_store is not None
            and self._progress.get(progress_key) == file_hash
        ):
            return "skipped"

        # Determine artifact type
        artifact_type = self._detect_artifact_type(file_path, content)

        # Build base metadata
        artifact_id = generate_artifact_id()
        now = datetime.now(timezone.utc).isoformat()
        metadata = {
            "artifact_id": artifact_id,
            "name": file_path.name,
            "original_filename": file_path.name,
            "artifact_type": artifact_type,
            "service": service,
            "file_path": str(file_path),
            "format": file_path.suffix.lstrip("."),
            "created_at": now,
            "updated_at": now,
            "tags": [],
            "useful_for": [],
            "entity_mentions": [],
            "description": "",
        }

        # LLM enrichment (adds description, tags, useful_for, entity_mentions,
        #                   brand, domain, feature, producer_agent, confidence)
        enriched = self._enrich_metadata(file_path, content, artifact_type, service)
        metadata.update(enriched)

        # Canonical name + write renamed copy to KB hierarchy (Gap 1)
        try:
            self._renamer.write_renamed_copy(file_path, metadata)
        except Exception as exc:
            # Non-fatal: still store the canonical name in metadata even if copy fails
            metadata["canonical_name"] = _build_canonical_name(
                metadata.get("brand", ""),
                metadata.get("domain", ""),
                metadata.get("feature", ""),
                artifact_type,
                file_path.suffix.lstrip("."),
            )
            print(f"  [WARN] Artifact renamer failed for {file_path.name}: {sanitize_error(str(exc))}")

        # Embed
        if self.vector_store is not None:
            self._embed_document(artifact_id, file_path, content, metadata, artifact_type)

        # Register
        self.registry.add_document(metadata)

        # Hypergraph — add artifact node
        self.hypergraph.add_node(artifact_id, metadata)

        # Placement agent — assign artifact to a feature-group node (Gap 3)
        try:
            self._placement_agent.place(artifact_id, metadata, self.hypergraph)
        except Exception as exc:
            print(f"  [WARN] Placement agent failed for {file_path.name}: {sanitize_error(str(exc))}")

        # Update progress
        self._progress[progress_key] = file_hash
        self._save_progress()

        print(f"  [OK] Ingested: {file_path.name} [{artifact_type}]")
        return "ingested"

    # ── Helpers ──────────────────────────────────────────────────────────────────

    def _detect_artifact_type(self, file_path: Path, content: str) -> str:
        name = file_path.name.lower()
        signals = {
            "brd": ["brd", "business_requirement"],
            "journey_map": ["journey", "flow"],
            "business_rules": ["rules", "business_rule"],
            "api_spec": ["api", "swagger", "openapi"],
            "feature_flag": ["feature_flag", "feature_toggle"],
            "gap_analysis": ["gap"],
            "risk_register": ["risk"],
        }
        for atype, keywords in signals.items():
            if any(kw in name for kw in keywords):
                return atype
        # Try content signals
        content_lower = content[:500].lower()
        for atype, keywords in signals.items():
            if any(kw in content_lower for kw in keywords):
                return atype
        return "document"

    def _enrich_metadata(
        self, file_path: Path, content: str, artifact_type: str, service: str
    ) -> Dict:
        """Call LLM to enrich metadata fields including brand, domain, feature."""
        try:
            client = self._get_client()
            prompt = ENRICH_PROMPT.format(
                artifact_type=artifact_type,
                filename=file_path.name,  # used in prompt, not flagged as unused
                service=service,
                content=content[:2000],
            )
            resp = client.messages.create(
                model=self.model,
                max_tokens=512,
                system=ENRICH_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = resp.content[0].text.strip()
            if raw.startswith("```"):
                parts = raw.split("```")
                raw = parts[1][4:] if parts[1].startswith("json") else parts[1]
            return json.loads(raw.strip())
        except Exception as exc:
            print(f"  [WARN] LLM enrichment failed for {file_path.name}: {sanitize_error(str(exc))}")
            return {}

    def _embed_document(
        self,
        artifact_id: str,
        file_path: Path,
        content: str,
        metadata: Dict,
        artifact_type: str,
    ):
        """Embed the document (with BRD chunking if applicable)."""
        is_brd = artifact_type in ("brd", "business_rules", "journey_map")

        if self.brd_chunking_enabled and self._chunker and is_brd:
            chunks = self._chunker.chunk(content, artifact_id)
            for i, chunk in enumerate(chunks):
                chunk_id = f"{artifact_id}_c{i}"
                chunk_meta = {
                    **{k: v for k, v in metadata.items() if isinstance(v, (str, int, float, bool))},
                    "chunk_index": i,
                    "heading": chunk.get("heading", ""),
                    "text": chunk["text"],
                }
                self.vector_store.add(chunk_id, chunk["text"], chunk_meta)
        else:
            flat_meta = {k: v for k, v in metadata.items() if isinstance(v, (str, int, float, bool))}
            flat_meta["text"] = content[:4000]
            self.vector_store.add(artifact_id, content[:4000], flat_meta)
