"""
LocalRAG — TF-IDF fallback retrieval directly from DocumentRegistry.
Used when vector scores are below the brute-force threshold or as a standalone offline mode.
"""
import math
import re
from collections import Counter
from typing import Dict, List, Tuple


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class LocalRAG:
    """TF-IDF based retrieval from a DocumentRegistry."""

    def __init__(self, registry):
        self._registry = registry

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float, Dict]]:
        """
        TF-IDF retrieval.
        Returns list of (artifact_id, score, metadata).
        """
        documents = self._registry.get_all_documents()
        if not documents:
            return []

        corpus = []
        for doc in documents:
            text_parts = [
                doc.get("name", ""),
                doc.get("description", ""),
                " ".join(doc.get("tags", [])),
                " ".join(doc.get("entity_mentions", [])),
                " ".join(doc.get("useful_for", [])),
            ]
            corpus.append(" ".join(filter(None, text_parts)))

        q_tokens = _tokenize(query)
        if not q_tokens:
            return []

        # Build IDF
        N = len(corpus)
        df: Counter = Counter()
        tokenized_corpus = []
        for doc_text in corpus:
            tokens = set(_tokenize(doc_text))
            tokenized_corpus.append(tokens)
            for t in tokens:
                df[t] += 1

        idf = {t: math.log((N + 1) / (df[t] + 1)) + 1 for t in df}

        # Score each document
        scored = []
        for i, (doc, tokens) in enumerate(zip(documents, tokenized_corpus)):
            score = sum(idf.get(t, 0) for t in q_tokens if t in tokens)
            if score > 0:
                scored.append((doc.get("artifact_id", ""), score, doc))

        scored.sort(key=lambda x: x[1], reverse=True)

        # Normalise scores 0-1
        if scored:
            max_score = scored[0][1]
            scored = [(aid, s / max_score, meta) for aid, s, meta in scored]

        return scored[:top_k]
