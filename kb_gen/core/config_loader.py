"""
KBStoreConfig — loads and validates kb_gen_config.yaml.
Candidate path discovery: CWD, bin/, env var KB_GEN_CONFIG_PATH, repo root walk.
Exposes all config values as attributes.
"""
import os
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:
    raise ImportError("pyyaml not installed. Run: pip install pyyaml>=6.0.1")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

_CANDIDATE_NAMES = ["kb_gen_config.yaml", "config/kb_gen_config.yaml"]


def _find_config(override: Optional[str] = None) -> Path:
    if override:
        p = Path(override)
        if p.exists():
            return p
        raise FileNotFoundError(f"Config not found at override path: {override}")

    env_path = os.getenv("KB_GEN_CONFIG_PATH")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p

    # Search CWD and up to 4 parents
    cwd = Path.cwd()
    for directory in [cwd, *cwd.parents[:4]]:
        for name in _CANDIDATE_NAMES:
            candidate = directory / name
            if candidate.exists():
                return candidate

    raise FileNotFoundError(
        "kb_gen_config.yaml not found. Set KB_GEN_CONFIG_PATH env var or place it in the project root."
    )


class KBStoreConfig:
    """Load and expose kb_gen_config.yaml values."""

    def __init__(self, config_path: Optional[str] = None):
        self._path = _find_config(config_path)
        self._base_dir = self._infer_base_dir(self._path)
        with open(self._path) as f:
            self._raw = yaml.safe_load(f) or {}
        self._validate()

    def _infer_base_dir(self, path: Path) -> Path:
        if path.parent.name == "bin":
            return path.parent.parent
        if path.parent.name in ("config", "kb_gen"):
            return path.parent.parent
        return path.parent

    def _validate(self):
        required = ["kb_root", "registry_path", "embeddings_db_path", "anthropic_model"]
        for key in required:
            if key not in self._raw:
                raise ValueError(f"kb_gen_config.yaml missing required key: '{key}'")

    # ── Paths ───────────────────────────────────────────────────────────────────
    @property
    def kb_root(self) -> Path:
        return self._base_dir / self._raw["kb_root"]

    @property
    def registry_path(self) -> Path:
        return self._base_dir / self._raw["registry_path"]

    @property
    def embeddings_path(self) -> Path:
        return self._base_dir / self._raw["embeddings_db_path"]

    @property
    def graph_path(self) -> Path:
        return self._base_dir / self._raw.get("graph_path", "KB/graph/hypergraph.json")

    @property
    def ingestion_progress_path(self) -> Path:
        return self._base_dir / self._raw.get("ingestion_progress_path", "logs/ingestion_progress.json")

    # ── LLM ─────────────────────────────────────────────────────────────────────
    @property
    def anthropic_model(self) -> str:
        return self._raw["anthropic_model"]

    @property
    def embedding_model(self) -> str:
        return self._raw.get("embedding_model", "all-MiniLM-L6-v2")

    @property
    def embedding_dimensions(self) -> int:
        return self._raw.get("embedding_dimensions", 384)

    # ── Chunking ────────────────────────────────────────────────────────────────
    @property
    def brd_chunk_max_chars(self) -> int:
        return self._raw.get("brd_chunk_max_chars", 1400)

    @property
    def brd_chunk_overlap_chars(self) -> int:
        return self._raw.get("brd_chunk_overlap_chars", 180)

    @property
    def brd_chunk_max_per_document(self) -> int:
        return self._raw.get("brd_chunk_max_per_document", 5000)

    # ── Ingestion ───────────────────────────────────────────────────────────────
    @property
    def json_ingestion_enabled(self) -> bool:
        return self._raw.get("json_ingestion_enabled", True)

    @property
    def json_included_files(self) -> list:
        return self._raw.get("json_included_files", [])

    # ── RAG ─────────────────────────────────────────────────────────────────────
    @property
    def top_k_sources(self) -> int:
        return self._raw.get("top_k_sources", 5)

    @property
    def use_graph_expansion(self) -> bool:
        return self._raw.get("use_graph_expansion", True)

    @property
    def strict_grounded(self) -> bool:
        return self._raw.get("strict_grounded", True)

    @property
    def use_brute_force_threshold(self) -> float:
        return self._raw.get("use_brute_force_threshold", 0.3)

    @property
    def enable_reranker(self) -> bool:
        return os.getenv("KB_STORE_ENABLE_RERANKER", "false").lower() == "true"

    # ── Raw access ──────────────────────────────────────────────────────────────
    @property
    def raw(self) -> dict:
        return self._raw

    def get(self, key: str, default=None):
        return self._raw.get(key, default)
