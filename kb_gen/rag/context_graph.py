"""
ContextGraph — session-level relationship graph.
Tracks which documents were retrieved together across multi-turn queries.
Used to improve retrieval coherence.
"""
from typing import Dict, List, Set


class ContextGraph:
    """In-memory graph for the lifetime of a query session."""

    def __init__(self):
        # adjacency: artifact_id -> set of co-retrieved artifact_ids
        self._adj: Dict[str, Set[str]] = {}
        self._query_count: int = 0

    def record_retrieval(self, artifact_ids: List[str]):
        """Record that these documents were retrieved together."""
        self._query_count += 1
        for aid in artifact_ids:
            if aid not in self._adj:
                self._adj[aid] = set()
            for other in artifact_ids:
                if other != aid:
                    self._adj[aid].add(other)

    def get_co_retrieved(self, artifact_id: str) -> List[str]:
        """Return documents frequently retrieved alongside this one."""
        return list(self._adj.get(artifact_id, set()))

    def suggest_expansion(self, artifact_ids: List[str]) -> List[str]:
        """Return additional document IDs likely relevant based on session history."""
        extra: Set[str] = set()
        for aid in artifact_ids:
            for neighbor in self.get_co_retrieved(aid):
                if neighbor not in artifact_ids:
                    extra.add(neighbor)
        return list(extra)

    def clear(self):
        self._adj.clear()
        self._query_count = 0

    @property
    def query_count(self) -> int:
        return self._query_count
