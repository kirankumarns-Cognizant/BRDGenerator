"""
FeedbackStore — persists human feedback records to KB/hitl/feedback.json.

record_feedback(artifact_id, query, useful, note): appends a feedback entry.
get_feedback(artifact_id): returns all feedback records for a document.

Each record: {artifact_id, query, useful, note, timestamp}
"""
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


class FeedbackStore:

    def __init__(self, store_path: str = "KB/hitl/feedback.json"):
        self._path = Path(store_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._records: List[Dict] = self._load()

    def _load(self) -> List[Dict]:
        if self._path.exists():
            try:
                with open(self._path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return []

    def _save(self):
        tmp = self._path.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(self._records, f, indent=2, default=str)
        shutil.move(str(tmp), str(self._path))

    def record_feedback(
        self,
        artifact_id: str,
        query: str,
        useful: bool,
        note: str = "",
        registry=None,
        intent: str = "",
    ):
        """Append a feedback record. Optionally propagates to DocumentRegistry."""
        record = {
            "artifact_id": artifact_id,
            "query": query,
            "useful": useful,
            "note": note,
            "intent": intent,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._records.append(record)
        self._save()

        if registry:
            intent_key = intent or "general"
            registry.update_usefulness(artifact_id, intent_key, useful)

    def get_feedback(self, artifact_id: str) -> List[Dict]:
        """Return all feedback records for a specific document."""
        return [r for r in self._records if r["artifact_id"] == artifact_id]

    def get_all(self) -> List[Dict]:
        return list(self._records)

    def count(self) -> int:
        return len(self._records)

    def summary(self) -> Dict:
        """Return usefulness summary per artifact_id."""
        stats: Dict[str, Dict] = {}
        for r in self._records:
            aid = r["artifact_id"]
            s = stats.setdefault(aid, {"total": 0, "useful": 0})
            s["total"] += 1
            if r.get("useful"):
                s["useful"] += 1
        return stats
