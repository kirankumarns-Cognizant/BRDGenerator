"""
DocumentMetadata — all tracked fields per document in the KB.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DocumentMetadata:
    # ── Base fields ────────────────────────────────────────────────────────────
    artifact_id: str = ""
    name: str = ""
    original_filename: str = ""
    artifact_type: str = ""          # journey_map | brd | api_spec | feature_flag | …
    producer_agent: str = ""
    producer_run_id: str = ""

    # ── Classification ─────────────────────────────────────────────────────────
    service: str = ""
    brand: str = ""
    domain: str = ""
    feature: str = ""

    # ── Document properties ────────────────────────────────────────────────────
    version: str = "1"
    format: str = ""                 # json | md | docx | …
    file_path: str = ""
    confidence: str = "MEDIUM"       # HIGH | MEDIUM | LOW

    # ── Timestamps ─────────────────────────────────────────────────────────────
    created_at: str = ""
    updated_at: str = ""

    # ── Lineage ────────────────────────────────────────────────────────────────
    client: str = ""
    derived_from: List[str] = field(default_factory=list)

    # ── LLM-enriched fields ────────────────────────────────────────────────────
    description: str = ""
    tags: List[str] = field(default_factory=list)
    useful_for: List[str] = field(default_factory=list)
    entity_mentions: List[str] = field(default_factory=list)
    notes: str = ""

    # ── Usage tracking ─────────────────────────────────────────────────────────
    used_for: List[str] = field(default_factory=list)
    query_intents: List[str] = field(default_factory=list)
    access_count: int = 0
    last_accessed: Optional[str] = None
    usefulness_scores: Dict[str, Dict] = field(default_factory=dict)
    # usefulness_scores[intent] = {"total": int, "useful": int}

    # ── Cross-service ──────────────────────────────────────────────────────────
    alias: List[str] = field(default_factory=list)
    entity_tags: List[str] = field(default_factory=list)
    cross_service_references: List[Dict] = field(default_factory=list)
    # cross_service_references = [{"service": str, "doc_id": str}]

    # ── Hypergraph ─────────────────────────────────────────────────────────────
    hypergraph_node_id: str = ""

    def to_dict(self) -> dict:
        import dataclasses
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "DocumentMetadata":
        import dataclasses
        valid_fields = {f.name for f in dataclasses.fields(cls)}
        filtered = {k: v for k, v in d.items() if k in valid_fields}
        return cls(**filtered)
