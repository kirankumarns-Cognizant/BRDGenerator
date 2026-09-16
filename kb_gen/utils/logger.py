"""Structured run logger for kb_gen operations."""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class KBLogger:
    def __init__(self, run_id: str, log_file: Optional[Path] = None):
        self.run_id = run_id
        self.log_file = log_file
        self.events: list = []

    def info(self, msg: str, **kw):
        self._log("INFO", msg, **kw)
        print(f"  {msg}")

    def success(self, msg: str, **kw):
        self._log("SUCCESS", msg, **kw)
        print(f"[OK] {msg}")

    def warning(self, msg: str, **kw):
        self._log("WARNING", msg, **kw)
        print(f"[WARN] {msg}")

    def error(self, msg: str, **kw):
        self._log("ERROR", msg, **kw)
        print(f"[ERROR] {msg}")

    def _log(self, level: str, msg: str, **kw):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": self.run_id,
            "level": level,
            "message": msg,
            **kw,
        }
        self.events.append(entry)
        if self.log_file:
            try:
                self.log_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.log_file, "a") as f:
                    f.write(json.dumps(entry) + "\n")
            except Exception:
                pass

    def get_events(self) -> list:
        return self.events

    def summary(self) -> dict:
        counts = {}
        for e in self.events:
            counts[e["level"]] = counts.get(e["level"], 0) + 1
        return {"run_id": self.run_id, "event_counts": counts, "total": len(self.events)}
