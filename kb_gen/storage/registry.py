"""
DocumentRegistry — catalog of all ingested documents.
Persisted as registry/documents.json.
Schema:
  {
    "documents": { "<artifact_id>": { ...DocumentMetadata fields... } },
    "services":  { "<service_name>": ["<artifact_id>", ...] }
  }
"""
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


class DocumentRegistry:

    def __init__(self, registry_path: str = "registry/documents.json"):
        self._path = Path(registry_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._data: Dict = self._load()

    # ── Persistence ─────────────────────────────────────────────────────────────

    def _load(self) -> Dict:
        if self._path.exists():
            try:
                with open(self._path) as f:
                    data = json.load(f)
                if "documents" not in data:
                    data["documents"] = {}
                if "services" not in data:
                    data["services"] = {}
                return data
            except (json.JSONDecodeError, OSError):
                pass
        return {"documents": {}, "services": {}}

    def _save(self):
        """Atomic write via temp file."""
        tmp = self._path.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(self._data, f, indent=2, default=str)
        shutil.move(str(tmp), str(self._path))

    # ── CRUD ────────────────────────────────────────────────────────────────────

    def add_document(self, metadata: dict) -> str:
        """
        Add or replace a document. Deduplicates by file_path — if a document
        with the same file_path already exists its artifact_id is reused.
        Returns the artifact_id.
        """
        file_path = metadata.get("file_path", "")
        if file_path:
            existing_ids = self.find_artifact_ids_by_file_path(file_path)
            if existing_ids:
                artifact_id = existing_ids[0]
                metadata["artifact_id"] = artifact_id
                # Remove old service index entry if service changed
                old = self._data["documents"].get(artifact_id, {})
                old_service = old.get("service", "")
                new_service = metadata.get("service", "")
                if old_service and old_service != new_service:
                    self._remove_from_service_index(artifact_id, old_service)

        artifact_id = metadata.get("artifact_id")
        if not artifact_id:
            from kb_gen.utils.artifact_id import generate_artifact_id
            artifact_id = generate_artifact_id()
            metadata["artifact_id"] = artifact_id

        metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._data["documents"][artifact_id] = metadata

        service = metadata.get("service", "")
        if service:
            svc_list = self._data["services"].setdefault(service, [])
            if artifact_id not in svc_list:
                svc_list.append(artifact_id)

        self._save()
        return artifact_id

    def get_document(self, artifact_id: str) -> Optional[Dict]:
        return self._data["documents"].get(artifact_id)

    def get_all_documents(self) -> List[Dict]:
        return list(self._data["documents"].values())

    def get_service_documents(self, service: str) -> List[Dict]:
        ids = self._data["services"].get(service, [])
        return [self._data["documents"][i] for i in ids if i in self._data["documents"]]

    def remove_document(self, artifact_id: str):
        doc = self._data["documents"].pop(artifact_id, None)
        if doc:
            service = doc.get("service", "")
            self._remove_from_service_index(artifact_id, service)
            self._save()

    def find_artifact_ids_by_file_path(self, file_path: str) -> List[str]:
        return [
            aid for aid, doc in self._data["documents"].items()
            if doc.get("file_path") == file_path
        ]

    def list_services(self) -> List[str]:
        return list(self._data["services"].keys())

    def count(self) -> int:
        return len(self._data["documents"])

    # ── Usefulness scoring ───────────────────────────────────────────────────────

    def update_used_for(self, artifact_id: str, task_type: str) -> None:
        """Append task_type to used_for list if not already present (Gap 8 write-back)."""
        doc = self._data["documents"].get(artifact_id)
        if not doc:
            return
        used_for = doc.setdefault("used_for", [])
        if task_type not in used_for:
            used_for.append(task_type)
            self._save()

    def update_usefulness(self, artifact_id: str, query_intent: str, useful: bool):
        doc = self._data["documents"].get(artifact_id)
        if not doc:
            return
        scores = doc.setdefault("usefulness_scores", {})
        bucket = scores.setdefault(query_intent, {"total": 0, "useful": 0})
        bucket["total"] += 1
        if useful:
            bucket["useful"] += 1
        doc["access_count"] = doc.get("access_count", 0) + 1
        doc["last_accessed"] = datetime.now(timezone.utc).isoformat()
        self._save()

    def record_access(self, artifact_id: str, intent: str = ""):
        doc = self._data["documents"].get(artifact_id)
        if not doc:
            return
        doc["access_count"] = doc.get("access_count", 0) + 1
        doc["last_accessed"] = datetime.now(timezone.utc).isoformat()
        if intent and intent not in doc.get("query_intents", []):
            doc.setdefault("query_intents", []).append(intent)
        self._save()

    # ── Helpers ─────────────────────────────────────────────────────────────────

    def _remove_from_service_index(self, artifact_id: str, service: str):
        if service in self._data["services"]:
            try:
                self._data["services"][service].remove(artifact_id)
            except ValueError:
                pass
            if not self._data["services"][service]:
                del self._data["services"][service]

    def get_all_tags(self) -> List[str]:
        tags = set()
        for doc in self._data["documents"].values():
            tags.update(doc.get("tags", []))
        return sorted(tags)

    def get_name_to_id_map(self) -> Dict[str, str]:
        return {
            doc.get("name", ""): aid
            for aid, doc in self._data["documents"].items()
            if doc.get("name")
        }
