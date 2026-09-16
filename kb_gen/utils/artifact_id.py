"""
Artifact ID — UUID + UTC timestamp.
Format: YYYYMMDD_HHMMSS_UTC_{uuid4_8chars}
Sortable by creation time. Unique across parallel runs in any timezone.
"""
import uuid
from datetime import datetime, timezone


def generate_artifact_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_UTC")
    short = str(uuid.uuid4()).replace("-", "")[:8]
    return f"{ts}_{short}"


def parse_artifact_id(artifact_id: str) -> dict:
    parts = artifact_id.split("_")
    if len(parts) < 4:
        return {"artifact_id": artifact_id, "valid": False}
    return {
        "artifact_id": artifact_id,
        "date": parts[0],
        "time": parts[1],
        "timezone": parts[2],
        "short_uuid": parts[3],
        "valid": True,
    }
