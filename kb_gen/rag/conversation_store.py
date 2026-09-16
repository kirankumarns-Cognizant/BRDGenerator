"""
ConversationStore — persists multi-turn conversation history for a query session.
"""
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


class ConversationStore:

    def __init__(self, store_path: str = "logs/conversations.json"):
        self._path = Path(store_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._sessions: Dict[str, List[Dict]] = self._load()

    def _load(self) -> Dict[str, List[Dict]]:
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
            json.dump(self._sessions, f, indent=2, default=str)
        shutil.move(str(tmp), str(self._path))

    def add_turn(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """Append a conversation turn."""
        turn = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if metadata:
            turn["metadata"] = metadata
        self._sessions.setdefault(session_id, []).append(turn)
        self._save()

    def get_history(self, session_id: str) -> List[Dict]:
        return self._sessions.get(session_id, [])

    def get_last_n(self, session_id: str, n: int = 5) -> List[Dict]:
        history = self._sessions.get(session_id, [])
        return history[-n:]

    def clear_session(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]
            self._save()

    def list_sessions(self) -> List[str]:
        return list(self._sessions.keys())
