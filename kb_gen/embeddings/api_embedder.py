"""
APIEmbedder — stub for future API-backed embedding service.
Falls back to LocalEmbedder immediately.
"""
from kb_gen.embeddings.local_embedder import LocalEmbedder


class APIEmbedder(LocalEmbedder):
    """Placeholder. Extend to call a remote embedding API."""
    pass
