"""
ArtifactRenamer — applies naming convention and writes renamed artifact to KB hierarchy.

Spec naming pattern:
  {brand}_{domain}_{feature}_{artifact_type}_v{version}.{ext}
  e.g. ST_service_ordering_Activation_brd_v1.json

The source file is NOT moved or deleted.  A renamed copy is written to:
  KB/{brand}/{domain}/{feature}/{canonical_name}

If brand/domain/feature are unknown a best-effort fallback path is used:
  KB/UNKNOWN/{service}/{artifact_type}/{canonical_name}

Usage:
  renamer = ArtifactRenamer(kb_root="KB")
  dest_path = renamer.write_renamed_copy(source_path, metadata)
  # metadata["file_path"] and metadata["canonical_name"] are updated in-place
"""
import re
import shutil
from pathlib import Path
from typing import Dict, Optional


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower().strip()).strip("_")


def build_canonical_name(
    brand: str,
    domain: str,
    feature: str,
    artifact_type: str,
    ext: str,
    version: int = 1,
) -> str:
    """Generate canonical filename following the spec naming convention."""
    parts = [
        (brand or "UNKNOWN").upper(),
        _slugify(domain or "UNKNOWN"),
        (feature or "UNKNOWN").replace(" ", "_"),
        _slugify(artifact_type or "document"),
        f"v{version}",
    ]
    suffix = f".{ext}" if ext else ".json"
    return "_".join(parts) + suffix


def build_kb_path(kb_root: Path, brand: str, domain: str, feature: str) -> Path:
    """Return the KB directory path for a given brand/domain/feature."""
    brand_slug = (brand or "UNKNOWN").upper()
    domain_slug = _slugify(domain or "UNKNOWN")
    feature_slug = (feature or "UNKNOWN").replace(" ", "_")
    return kb_root / brand_slug / domain_slug / feature_slug


class ArtifactRenamer:
    """Writes a renamed copy of each artifact into the KB brand/domain/feature hierarchy."""

    def __init__(self, kb_root: str = "KB"):
        self._kb_root = Path(kb_root)

    def write_renamed_copy(
        self, source_path: Path, metadata: Dict, version: int = 1
    ) -> Optional[Path]:
        """Copy source_path to KB hierarchy with canonical name.

        Updates metadata["canonical_name"] and metadata["kb_canonical_path"] in-place.
        Returns the destination path, or None if the file already exists unchanged.
        """
        brand = metadata.get("brand", "")
        domain = metadata.get("domain", "")
        feature = metadata.get("feature", "")
        artifact_type = metadata.get("artifact_type", "document")
        ext = source_path.suffix.lstrip(".")

        canonical = build_canonical_name(brand, domain, feature, artifact_type, ext, version)
        dest_dir = build_kb_path(self._kb_root, brand, domain, feature)
        dest_path = dest_dir / canonical

        # Skip copy if destination already matches source (file already in correct place)
        if dest_path.resolve() == source_path.resolve():
            metadata["canonical_name"] = canonical
            metadata["kb_canonical_path"] = str(dest_path)
            return dest_path

        # Skip copy if destination already exists and is identical (idempotent re-ingest)
        if dest_path.exists() and dest_path.stat().st_size == source_path.stat().st_size:
            metadata["canonical_name"] = canonical
            metadata["kb_canonical_path"] = str(dest_path)
            return dest_path

        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(source_path), str(dest_path))

        metadata["canonical_name"] = canonical
        metadata["kb_canonical_path"] = str(dest_path)
        return dest_path

    def canonical_name(self, metadata: Dict) -> str:
        """Return the canonical name for an artifact without writing any files."""
        return build_canonical_name(
            metadata.get("brand", ""),
            metadata.get("domain", ""),
            metadata.get("feature", ""),
            metadata.get("artifact_type", "document"),
            metadata.get("format", "json"),
        )
