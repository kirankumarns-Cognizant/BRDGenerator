"""
ChromaDBStore — wraps ChromaDB persistent client.

VegasEmbeddingFunction: ChromaDB EmbeddingFunction backed by VegasEmbeddingService
(Gemini embeddings) when pyvegas is available; falls back to LocalEmbedder otherwise.

ChromaDBStore.add(artifact_id, text, metadata): embed and store.
ChromaDBStore.query(text, top_k): ANN search returning (artifact_id, score, metadata) tuples.
"""
from typing import Dict, List, Optional, Tuple


try:
    import chromadb
    from chromadb import EmbeddingFunction, Documents, Embeddings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    EmbeddingFunction = object
    Documents = list
    Embeddings = list


class VegasEmbeddingFunction(EmbeddingFunction if CHROMADB_AVAILABLE else object):
    """
    ChromaDB EmbeddingFunction. Uses VegasEmbeddingService (Gemini) if available;
    falls back to LocalEmbedder (sentence-transformers).
    """
    MAX_BATCH = 24
    MAX_RETRIES = 2

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model_name = model_name
        self._backend = self._init_backend()

    def _init_backend(self):
        try:
            from pyvegas.langx.emas import VegasEmbeddingService
            return VegasEmbeddingService()
        except ImportError:
            pass
        from kb_gen.embeddings.local_embedder import LocalEmbedder
        return LocalEmbedder(self._model_name)

    def __call__(self, input: Documents) -> Embeddings:
        results = []
        for i in range(0, len(input), self.MAX_BATCH):
            batch = input[i: i + self.MAX_BATCH]
            for attempt in range(self.MAX_RETRIES + 1):
                try:
                    if hasattr(self._backend, "embed_batch"):
                        vecs = self._backend.embed_batch(batch)
                    else:
                        vecs = [self._backend.embed(t) for t in batch]
                    results.extend(vecs)
                    break
                except Exception as exc:
                    if attempt == self.MAX_RETRIES:
                        raise RuntimeError(f"Embedding failed after {self.MAX_RETRIES} retries: {exc}") from exc
        return results


class ChromaDBStore:
    """Vector store operations backed by ChromaDB."""

    COLLECTION_NAME = "kb_documents"

    def __init__(
        self,
        db_path: str = "kb_store",
        collection_name: str = COLLECTION_NAME,
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        if not CHROMADB_AVAILABLE:
            raise ImportError("chromadb not installed. Run: pip install chromadb>=0.5.0")
        import chromadb as _chromadb
        from pathlib import Path
        Path(db_path).mkdir(parents=True, exist_ok=True)
        self._client = _chromadb.PersistentClient(path=db_path)
        self._ef = VegasEmbeddingFunction(model_name=embedding_model)
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            embedding_function=self._ef,
            metadata={"hnsw:space": "cosine"},
        )
        self._collection_name = collection_name

    def add(self, artifact_id: str, text: str, metadata: Optional[Dict] = None):
        """Embed and store a document chunk."""
        safe_meta = {}
        if metadata:
            for k, v in metadata.items():
                if isinstance(v, (str, int, float, bool)):
                    safe_meta[k] = v
                elif v is None:
                    pass
                else:
                    safe_meta[k] = str(v)
        try:
            self._collection.upsert(
                documents=[text],
                metadatas=[safe_meta],
                ids=[artifact_id],
            )
        except Exception as exc:
            raise RuntimeError(f"ChromaDB upsert failed for {artifact_id}: {exc}") from exc

    def query_filtered(
        self, text: str, artifact_ids: List[str], top_k: int = 5
    ) -> List[Tuple[str, float, Dict]]:
        """Targeted ANN search restricted to artifacts whose metadata artifact_id is in the list.

        ChromaDB chunks are stored with metadata field 'artifact_id' equal to the base artifact
        ID (without chunk suffix). We filter on that field so all chunks of a targeted artifact
        are included.  Falls back to global query if the filtered result set is empty.
        """
        if not artifact_ids:
            return self.query(text, top_k=top_k)
        try:
            where = {"artifact_id": {"$in": artifact_ids}}
            results = self._collection.query(
                query_texts=[text],
                n_results=min(top_k, max(1, self._collection.count())),
                where=where,
                include=["documents", "metadatas", "distances"],
            )
        except Exception:
            return self.query(text, top_k=top_k)

        ids = (results.get("ids") or [[]])[0]
        distances = (results.get("distances") or [[]])[0]
        metas = (results.get("metadatas") or [[]])[0]

        output = []
        for doc_id, dist, meta in zip(ids, distances, metas):
            score = max(0.0, 1.0 - dist / 2.0)
            output.append((doc_id, score, meta or {}))
        return output

    def query(self, text: str, top_k: int = 5) -> List[Tuple[str, float, Dict]]:
        """
        ANN search.
        Returns list of (artifact_id, cosine_score, metadata).
        Cosine score is normalized 0-1 (1 = identical).
        """
        try:
            results = self._collection.query(
                query_texts=[text],
                n_results=min(top_k, max(1, self._collection.count())),
                include=["documents", "metadatas", "distances"],
            )
        except Exception:
            return []

        ids = (results.get("ids") or [[]])[0]
        distances = (results.get("distances") or [[]])[0]
        metas = (results.get("metadatas") or [[]])[0]

        output = []
        for doc_id, dist, meta in zip(ids, distances, metas):
            # Convert cosine distance (0=identical, 2=opposite) to score (1=identical, 0=opposite)
            score = max(0.0, 1.0 - dist / 2.0)
            output.append((doc_id, score, meta or {}))
        return output

    def delete(self, artifact_id: str):
        try:
            self._collection.delete(ids=[artifact_id])
        except Exception:
            pass

    def count(self) -> int:
        try:
            return self._collection.count()
        except Exception:
            return 0

    def get_collection_name(self) -> str:
        return self._collection_name
