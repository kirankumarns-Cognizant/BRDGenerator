"""
LocalEmbedder — sentence-transformers embedder with TF-IDF hash fallback.

If the sentence-transformers model cannot be loaded (no internet, corporate proxy),
falls back to a deterministic hash-based embedding so the pipeline keeps running
without any network access. Sets HF_HUB_OFFLINE=1 before importing the library so
the huggingface_hub retry loop never fires.
"""
import hashlib
import math
import os
from typing import List

# Set BEFORE importing sentence_transformers / huggingface_hub so that the
# library skips all network requests and fails fast on a cache miss.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

_model = None
_model_failed = False


def _get_model(model_name: str = "all-MiniLM-L6-v2"):
    global _model, _model_failed
    if _model_failed:
        return None
    if _model is not None:
        return _model
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(model_name)
    except Exception:
        _model_failed = True
        return None
    return _model


def _hash_embed(text: str, dim: int = 384) -> List[float]:
    """Deterministic pseudo-embedding via SHA-256 token hashing (TF-IDF-like)."""
    tokens = text.lower().split()
    vec = [0.0] * dim
    for tok in tokens:
        h = hashlib.sha256(tok.encode()).digest()
        for i in range(min(dim, len(h))):
            vec[i % dim] += (h[i] / 127.5) - 1.0
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


class LocalEmbedder:
    """Wraps sentence-transformers; falls back to hash embedding when unavailable."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._use_fallback = False

    def _ensure_model(self):
        if self._use_fallback:
            return
        if self._model is None:
            self._model = _get_model(self.model_name)
            if self._model is None:
                self._use_fallback = True
                print(
                    "[LocalEmbedder] sentence-transformers model unavailable "
                    "(not cached / offline mode). Using hash-based fallback embeddings."
                )

    def embed(self, text: str) -> List[float]:
        self._ensure_model()
        if self._use_fallback:
            return _hash_embed(text)
        vec = self._model.encode(text, normalize_embeddings=True)
        return vec.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        self._ensure_model()
        if self._use_fallback:
            return [_hash_embed(t) for t in texts]
        vecs = self._model.encode(texts, normalize_embeddings=True, batch_size=32)
        return [v.tolist() for v in vecs]
