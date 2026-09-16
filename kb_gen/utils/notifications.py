"""
NotificationWriter — appends async placement review items to KB/graph/notifications.json.

The placement agent and conflict resolver write here when they need human review.
The pipeline never blocks on notifications — they are async and reviewed periodically.

Schema per notification:
{
  "notification_id":    str,       # notif_{timestamp}_{counter}
  "type":               str,       # TEMP_NODE_REVIEW | MERGE_PROPOSAL | NEW_HYPEREDGE_REVIEW | CONFLICT
  "priority":           str,       # LOW | MEDIUM | HIGH
  "status":             str,       # PENDING | REVIEWED | RESOLVED
  "created_at":         ISO UTC str,
  "artifact_id":        str,
  "artifact_name":      str,
  "placement_context":  str,       # full reasoning from placement agent
  "candidate_nodes":    [...],     # nodes considered with similarity scores
  "recommended_action": str,
  "human_decision":     str,       # human fills this in
  "resolved_at":        str
}
"""
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


_counter = 0


def _next_id() -> str:
    global _counter
    _counter += 1
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"notif_{ts}_{_counter:03d}"


class NotificationWriter:
    """Appends structured notification records to KB/graph/notifications.json."""

    def __init__(self, notifications_path: str = "KB/graph/notifications.json"):
        self._path = Path(notifications_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def write(
        self,
        notif_type: str,
        artifact_id: str,
        artifact_name: str,
        placement_context: str,
        candidate_nodes: Optional[List[Dict]] = None,
        recommended_action: str = "",
        priority: str = "MEDIUM",
    ) -> str:
        """Append one notification. Returns the notification_id."""
        notif_id = _next_id()
        entry = {
            "notification_id": notif_id,
            "type": notif_type,
            "priority": priority,
            "status": "PENDING",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "artifact_id": artifact_id,
            "artifact_name": artifact_name,
            "placement_context": placement_context,
            "candidate_nodes": candidate_nodes or [],
            "recommended_action": recommended_action,
            "human_decision": "",
            "resolved_at": "",
        }
        try:
            existing = self._read()
            existing.append(entry)
            self._write(existing)
        except Exception:
            pass  # never block the pipeline
        return notif_id

    def pending(self) -> List[Dict]:
        return [n for n in self._read() if n.get("status") == "PENDING"]

    def resolve(self, notification_id: str, decision: str) -> bool:
        """Mark a notification as resolved with a human decision."""
        entries = self._read()
        for entry in entries:
            if entry.get("notification_id") == notification_id:
                entry["status"] = "RESOLVED"
                entry["human_decision"] = decision
                entry["resolved_at"] = datetime.now(timezone.utc).isoformat()
                self._write(entries)
                return True
        return False

    def _read(self) -> List[Dict]:
        if self._path.exists():
            try:
                with open(self._path, encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    return data.get("notifications", [])
                return data if isinstance(data, list) else []
            except (json.JSONDecodeError, OSError):
                pass
        return []

    def _write(self, entries: List[Dict]) -> None:
        tmp = self._path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"notifications": entries}, f, indent=2, default=str)
        shutil.move(str(tmp), str(self._path))
