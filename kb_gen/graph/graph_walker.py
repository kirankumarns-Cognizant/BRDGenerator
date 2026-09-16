"""
GraphWalker — graph expansion during RAG retrieval.

Given a seed set of artifact IDs, walks hypergraph edges to find related documents.
Optionally re-queries ChromaDB for each related node.
"""
from typing import List, Optional


class GraphWalker:

    def __init__(self, vector_store, hypergraph):
        self.vector_store = vector_store
        self.hypergraph = hypergraph

    def expand(
        self,
        artifact_ids: List[str],
        max_depth: int = 2,
        max_expanded: int = 10,
        edge_types: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Given seed artifact_ids, walk hypergraph edges to find related documents.
        Returns a deduplicated list of related artifact_ids (excluding seeds).
        """
        expanded = []
        seen = set(artifact_ids)

        for seed_id in artifact_ids:
            related = self.hypergraph.find_related(
                seed_id,
                edge_types=edge_types,
                max_depth=max_depth,
            )
            for rid in related:
                if rid not in seen:
                    expanded.append(rid)
                    seen.add(rid)
                if len(expanded) >= max_expanded:
                    break
            if len(expanded) >= max_expanded:
                break

        return expanded
