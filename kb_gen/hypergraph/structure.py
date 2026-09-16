"""
DocumentHypergraph — cross-service document relationship graph.
Persisted as KB/graph/hypergraph.json with atomic backup.

Schema:
{
  "nodes": {
    "<artifact_id>": {
      "artifact_id": str,
      "name": str,
      "artifact_type": str,
      "service": str,
      "brand": str,       # e.g. ST | TW | SHARED
      "domain": str,      # e.g. service_ordering
      "feature": str,     # e.g. Activation
      "tags": []
    }
  },
  "edges": [
    {
      "from": str,
      "to": str,
      "edge_type": "references|informs|supersedes|related",
      "weight": float
    }
  ],
  "alias_index": {
    "<term>": ["<artifact_id>", ...]   // term → artifact_ids for targeted search
  }
}
"""
import json
import re
import shutil
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Set


VALID_EDGE_TYPES = {"references", "informs", "supersedes", "related"}
_STOP_WORDS = {"the", "a", "an", "is", "are", "in", "of", "for", "to", "and", "or",
               "what", "how", "why", "when", "does", "do", "i", "we", "it", "this"}


class DocumentHypergraph:

    def __init__(self, graph_path: str = "KB/graph/hypergraph.json"):
        self._path = Path(graph_path)
        self._backup = self._path.with_name(self._path.stem + ".backup.json")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._data: Dict = self._load()
        # Internal edge dedup index: (from, to, edge_type) → True
        self._edge_key_index: Set = self._build_edge_index()

    # ── Persistence ─────────────────────────────────────────────────────────────

    def _load(self) -> Dict:
        for candidate in [self._path, self._backup]:
            if candidate.exists():
                try:
                    with open(candidate) as f:
                        data = json.load(f)
                    # Normalize legacy nodes schema: list → dict keyed by id
                    if isinstance(data.get("nodes"), list):
                        data["nodes"] = {
                            n["id"]: {
                                "artifact_id": n.get("id", ""),
                                "name": n.get("label", n.get("id", "")),
                                "artifact_type": n.get("type", "document"),
                                "service": n.get("properties", {}).get("service", ""),
                                "tags": n.get("properties", {}).get("tags", []),
                            }
                            for n in data["nodes"]
                            if "id" in n
                        }
                    if "nodes" not in data:
                        data["nodes"] = {}
                    if "alias_index" not in data:
                        data["alias_index"] = {}
                    if "edges" not in data:
                        data["edges"] = []
                    # Normalize legacy edge schema (source/target/type → from/to/edge_type)
                    normalized = []
                    for e in data["edges"]:
                        if "from" not in e:
                            e = {
                                "from": e.get("source", ""),
                                "to": e.get("target", ""),
                                "edge_type": e.get("type", "related"),
                                "weight": e.get("weight", 1.0),
                            }
                        normalized.append(e)
                    data["edges"] = normalized
                    return data
                except (json.JSONDecodeError, OSError):
                    continue
        return {"nodes": {}, "edges": [], "alias_index": {}}

    def _save(self):
        """Atomic write; backup the previous version first."""
        tmp = self._path.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(self._data, f, indent=2, default=str)
        if self._path.exists():
            shutil.copy2(str(self._path), str(self._backup))
        shutil.move(str(tmp), str(self._path))

    def _build_edge_index(self) -> Set:
        index = set()
        for e in self._data.get("edges", []):
            key = (e["from"], e["to"], e["edge_type"])
            index.add(key)
        return index

    # ── Nodes ────────────────────────────────────────────────────────────────────

    def add_node(self, artifact_id: str, metadata: dict):
        """Add or update a node and index its terms in the alias_index."""
        self._data["nodes"][artifact_id] = {
            "artifact_id": artifact_id,
            "name": metadata.get("name", ""),
            "artifact_type": metadata.get("artifact_type", ""),
            "service": metadata.get("service", ""),
            "brand": metadata.get("brand", ""),
            "domain": metadata.get("domain", ""),
            "feature": metadata.get("feature", ""),
            "tags": metadata.get("tags", []),
        }
        self._update_alias_index(artifact_id, metadata)
        self._save()

    # ── Alias index ──────────────────────────────────────────────────────────────

    def _update_alias_index(self, artifact_id: str, metadata: dict):
        """Index searchable terms from artifact metadata into alias_index."""
        terms: List[str] = []
        for field in ("service", "brand", "domain", "feature", "artifact_type"):
            val = metadata.get(field, "")
            if val:
                terms.append(val.lower().replace("_", " "))
                terms.append(val.lower())  # also index with underscores intact
        for tag in metadata.get("tags", []):
            if tag:
                terms.append(tag.lower())
        # Index entity mentions
        for entity in metadata.get("entity_mentions", []):
            if entity:
                terms.append(entity.lower())

        idx = self._data.setdefault("alias_index", {})
        for term in terms:
            term = term.strip()
            if not term:
                continue
            ids = idx.setdefault(term, [])
            if artifact_id not in ids:
                ids.append(artifact_id)

    @staticmethod
    def _tokenize(query: str) -> List[str]:
        """Lowercase, split on non-alphanumeric, remove stop-words."""
        tokens = re.sub(r"[^a-z0-9 ]", " ", query.lower()).split()
        return [t for t in tokens if t not in _STOP_WORDS and len(t) > 1]

    def alias_lookup(self, query: str, max_results: int = 20) -> List[str]:
        """Return artifact_ids whose alias terms match query words, ranked by hit count.

        Uses a word-overlap strategy: each query token is looked up in the alias_index
        and matching artifact_ids are scored by frequency. Returns the top max_results.
        """
        tokens = self._tokenize(query)
        if not tokens:
            return []

        idx = self._data.get("alias_index", {})
        scores: Counter = Counter()

        for token in tokens:
            # Exact term match
            for aid in idx.get(token, []):
                scores[aid] += 2  # exact match scores higher
            # Prefix / substring match (for partial terms)
            for term, aids in idx.items():
                if token in term and term != token:
                    for aid in aids:
                        scores[aid] += 1

        return [aid for aid, _ in scores.most_common(max_results)]

    def get_node(self, artifact_id: str) -> Optional[Dict]:
        return self._data["nodes"].get(artifact_id)

    def list_nodes(self) -> List[Dict]:
        return list(self._data["nodes"].values())

    def remove_node(self, artifact_id: str):
        self._data["nodes"].pop(artifact_id, None)
        # Remove all edges involving this node
        self._data["edges"] = [
            e for e in self._data["edges"]
            if e["from"] != artifact_id and e["to"] != artifact_id
        ]
        self._edge_key_index = self._build_edge_index()
        self._save()

    # ── Edges ────────────────────────────────────────────────────────────────────

    def add_edge(self, from_id: str, to_id: str, edge_type: str = "related", weight: float = 1.0):
        """Add a directed edge. Deduplicates via _edge_key_index."""
        if edge_type not in VALID_EDGE_TYPES:
            edge_type = "related"
        key = (from_id, to_id, edge_type)
        if key in self._edge_key_index:
            return  # Already exists
        self._data["edges"].append({"from": from_id, "to": to_id, "edge_type": edge_type, "weight": weight})
        self._edge_key_index.add(key)
        self._save()

    def list_edges(self) -> List[Dict]:
        return list(self._data["edges"])

    # ── Graph traversal ──────────────────────────────────────────────────────────

    def find_related(
        self,
        artifact_id: str,
        edge_types: Optional[List[str]] = None,
        max_depth: int = 2,
    ) -> List[str]:
        """
        BFS walk to find related artifact IDs from a seed node.
        Returns a list of related IDs (excluding the seed itself).
        """
        allowed = set(edge_types) if edge_types else VALID_EDGE_TYPES
        visited: Set[str] = set()
        queue = [(artifact_id, 0)]
        results = []

        while queue:
            current, depth = queue.pop(0)
            if current in visited or depth > max_depth:
                continue
            visited.add(current)
            if current != artifact_id:
                results.append(current)

            for edge in self._data["edges"]:
                if edge["from"] == current and edge["edge_type"] in allowed:
                    neighbor = edge["to"]
                    if neighbor not in visited:
                        queue.append((neighbor, depth + 1))

        return results

    def get_neighbors(self, artifact_id: str) -> List[str]:
        return [e["to"] for e in self._data["edges"] if e["from"] == artifact_id]

    def node_count(self) -> int:
        return len(self._data["nodes"])

    def edge_count(self) -> int:
        return len(self._data["edges"])

    @property
    def raw(self) -> Dict:
        return self._data
