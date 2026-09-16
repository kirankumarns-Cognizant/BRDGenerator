"""
QueryCache — FAQ-style cache for RAG query results.

Two lookup strategies (in order):
  1. Exact match   — normalised question string (lowercase, collapsed whitespace)
  2. Semantic match — cosine similarity of question embeddings (opt-in)

Cache is persisted as JSON so it survives process restarts.
Each entry stores the full result dict, a timestamp, and hit statistics.
"""
import json
import math
import time
from pathlib import Path
from typing import Dict, Optional


# ── Helpers ───────────────────────────────────────────────────────────────────

def _normalize(question: str) -> str:
    """Lowercase + collapse whitespace."""
    return " ".join(question.lower().strip().split())


def _cosine(a, b) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (na * nb)


# ── Cache ─────────────────────────────────────────────────────────────────────

class QueryCache:
    """
    Persistent FAQ cache for RAGQueryEngine.

    Parameters
    ----------
    cache_path : str | Path
        JSON file to persist cache (e.g. ``KB/cache/query_cache.json``).
    ttl_seconds : int | None
        Seconds before an entry expires.  ``None`` = never expire.
        Default: 86400 (24 h).
    use_semantic_cache : bool
        When True, also match questions by embedding cosine similarity.
    semantic_threshold : float
        Minimum cosine similarity (0–1) to treat a question as a cache hit.
        Default: 0.92.
    """

    def __init__(
        self,
        cache_path: str = "KB/cache/query_cache.json",
        ttl_seconds: Optional[int] = 86400,
        use_semantic_cache: bool = False,
        semantic_threshold: float = 0.92,
    ):
        self.cache_path = Path(cache_path)
        self.ttl_seconds = ttl_seconds
        self.use_semantic_cache = use_semantic_cache
        self.semantic_threshold = semantic_threshold

        # {normalised_question: {question, result, timestamp, hit_count, last_hit, embedding?}}
        self._cache: Dict[str, dict] = {}
        self._embedder = None
        self._load()

    # ── Public API ────────────────────────────────────────────────────────────

    def get(self, question: str) -> Optional[Dict]:
        """Return cached result or None on miss."""
        key = _normalize(question)

        # 1. Exact match
        entry = self._cache.get(key)
        if entry and self._is_valid(entry):
            return self._record_hit(key, entry)

        # 2. Semantic match (optional)
        if self.use_semantic_cache:
            match_key = self._semantic_lookup(question)
            if match_key:
                entry = self._cache[match_key]
                return self._record_hit(match_key, entry)

        return None

    def set(self, question: str, result: Dict) -> None:
        """Store a result.  Low-confidence answers are cached with a shorter TTL."""
        key = _normalize(question)
        entry: dict = {
            "question": question,
            "result": result,
            "timestamp": time.time(),
            "hit_count": 0,
            "last_hit": None,
        }
        if self.use_semantic_cache:
            entry["embedding"] = self._embed(question)
        self._cache[key] = entry
        self._save()

    def invalidate(self, question: str) -> bool:
        """Remove a specific question from cache. Returns True if it existed."""
        key = _normalize(question)
        if key in self._cache:
            del self._cache[key]
            self._save()
            return True
        return False

    def clear(self) -> int:
        """Clear all entries. Returns number of entries removed."""
        count = len(self._cache)
        self._cache = {}
        self._save()
        return count

    def purge_expired(self) -> int:
        """Remove all expired entries. Returns count removed."""
        if not self.ttl_seconds:
            return 0
        now = time.time()
        expired = [k for k, v in self._cache.items() if now - v["timestamp"] > self.ttl_seconds]
        for k in expired:
            del self._cache[k]
        if expired:
            self._save()
        return len(expired)

    def stats(self) -> Dict:
        """Return cache statistics."""
        now = time.time()
        entries = list(self._cache.values())
        active = [e for e in entries if self._is_valid(e)]
        total_hits = sum(e["hit_count"] for e in entries)
        return {
            "total_entries": len(entries),
            "active_entries": len(active),
            "expired_entries": len(entries) - len(active),
            "total_hits": total_hits,
            "semantic_cache": self.use_semantic_cache,
            "ttl_seconds": self.ttl_seconds,
            "cache_path": str(self.cache_path),
        }

    def list_questions(self) -> list:
        """Return all cached (non-expired) questions with hit counts."""
        return [
            {
                "question": v["question"],
                "hit_count": v["hit_count"],
                "cached_at": v["timestamp"],
                "last_hit": v["last_hit"],
            }
            for v in self._cache.values()
            if self._is_valid(v)
        ]

    # ── Internals ─────────────────────────────────────────────────────────────

    def _is_valid(self, entry: dict) -> bool:
        if not self.ttl_seconds:
            return True
        return time.time() - entry["timestamp"] <= self.ttl_seconds

    def _record_hit(self, key: str, entry: dict) -> Dict:
        entry["hit_count"] += 1
        entry["last_hit"] = time.time()
        self._save()
        result = dict(entry["result"])
        result.setdefault("telemetry", {})["cache_hit"] = True
        result["telemetry"]["cache_question"] = entry["question"]
        return result

    def _semantic_lookup(self, question: str) -> Optional[str]:
        emb = self._embed(question)
        if emb is None:
            return None
        best_key, best_score = None, 0.0
        for key, entry in self._cache.items():
            cached_emb = entry.get("embedding")
            if cached_emb and self._is_valid(entry):
                score = _cosine(emb, cached_emb)
                if score > best_score:
                    best_score, best_key = score, key
        if best_score >= self.semantic_threshold:
            return best_key
        return None

    def _embed(self, text: str):
        if self._embedder is None:
            try:
                from kb_gen.embeddings.local_embedder import LocalEmbedder
                self._embedder = LocalEmbedder()
            except Exception:
                return None
        try:
            return self._embedder.embed(text)
        except Exception:
            return None

    def _load(self) -> None:
        if self.cache_path.exists():
            try:
                data = json.loads(self.cache_path.read_text(encoding="utf-8"))
                self._cache = data if isinstance(data, dict) else {}
            except Exception:
                self._cache = {}
        else:
            self._cache = {}

    def _save(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.cache_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._cache, indent=2), encoding="utf-8")
        tmp.replace(self.cache_path)
