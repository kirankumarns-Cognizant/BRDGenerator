"""
SmartCache — SHA256-based change detection to avoid re-embedding unchanged documents.
Persisted as a JSON sidecar next to the embeddings DB.
"""
import hashlib
import json
import shutil
from pathlib import Path
from typing import Dict


class SmartCache:

    def __init__(self, cache_path: str = "kb_store/.smart_cache.json"):
        self._path = Path(cache_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, str] = self._load()

    def _load(self) -> Dict[str, str]:
        if self._path.exists():
            try:
                with open(self._path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def _save(self):
        tmp = self._path.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(self._cache, f, indent=2)
        shutil.move(str(tmp), str(self._path))

    @staticmethod
    def _hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def needs_update(self, artifact_id: str, text: str) -> bool:
        """Return True if the text changed or has never been embedded."""
        return self._cache.get(artifact_id) != self._hash(text)

    def mark_embedded(self, artifact_id: str, text: str):
        """Record that this text has been embedded."""
        self._cache[artifact_id] = self._hash(text)
        self._save()

    def invalidate(self, artifact_id: str):
        if artifact_id in self._cache:
            del self._cache[artifact_id]
            self._save()

    def clear(self):
        self._cache.clear()
        self._save()
