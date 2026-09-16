"""
QueryLogger — appends every RAG query to KB/cache/query_log.json.

Spec purpose: seed the Phase 2 FAQ cache. Every query logged now becomes
training/seed data for the semantic FAQ cache.

Schema per entry:
{
  "query_text":        str,
  "timestamp":         ISO UTC str,
  "session_id":        str,
  "intent":            str,
  "source_artifact_ids": [str, ...],
  "answer_summary":    str,       # first 300 chars of answer
  "elapsed_sec":       float,
  "was_useful":        null | bool,  # filled in later via HITL
  "retrieval_method":  str        # "targeted" | "vector" | "hybrid" | "local"
}
"""
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


class QueryLogger:
    """Appends structured query records to a JSON log file."""

    def __init__(self, log_path: str = "KB/cache/query_log.json"):
        self._path = Path(log_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        query_text: str,
        intent: str,
        sources: List[Dict],
        answer: str,
        elapsed_sec: float,
        session_id: str = "",
        retrieval_method: str = "vector",
        was_useful: Optional[bool] = None,
    ) -> None:
        """Append one query entry to the log. Silently no-ops on write errors."""
        entry = {
            "query_text": query_text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "intent": intent,
            "source_artifact_ids": [s.get("artifact_id", "") for s in sources if s.get("artifact_id")],
            "answer_summary": answer[:300],
            "elapsed_sec": round(elapsed_sec, 2),
            "was_useful": was_useful,
            "retrieval_method": retrieval_method,
        }
        try:
            existing = self._read()
            existing.append(entry)
            self._write(existing)
        except Exception:
            pass  # never crash the query pipeline on log write failure

    def _read(self) -> List[Dict]:
        if self._path.exists():
            try:
                with open(self._path, encoding="utf-8") as f:
                    data = json.load(f)
                return data if isinstance(data, list) else []
            except (json.JSONDecodeError, OSError):
                pass
        return []

    def _write(self, entries: List[Dict]) -> None:
        tmp = self._path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, default=str)
        shutil.move(str(tmp), str(self._path))

    def count(self) -> int:
        return len(self._read())
