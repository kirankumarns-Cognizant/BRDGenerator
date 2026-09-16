"""
SimpleSearch — keyword search helper for quick document lookup by name/tag.
"""
import re
from typing import Dict, List


class SimpleSearch:

    def __init__(self, registry):
        self._registry = registry

    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        Simple substring/keyword search across document name, tags, description.
        Returns list of matching document dicts ordered by match quality.
        """
        q = query.lower()
        q_tokens = set(re.findall(r"[a-z0-9]+", q))
        scored = []

        for doc in self._registry.get_all_documents():
            score = 0
            name = (doc.get("name") or "").lower()
            desc = (doc.get("description") or "").lower()
            tags = " ".join(doc.get("tags", [])).lower()

            if q in name:
                score += 10
            if q in desc:
                score += 5
            if q in tags:
                score += 3

            for tok in q_tokens:
                if tok in name:
                    score += 2
                if tok in desc:
                    score += 1
                if tok in tags:
                    score += 1

            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:top_k]]
