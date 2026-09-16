"""
LateChunker — contextual chunk generation from retrieved documents.

Generates chunks that include surrounding sentence context.
Parameters:
  min_chunk_size (default 150)
  max_chunk_size (default 1500)
  context_sentences (default 3)
"""
import re
from typing import Dict, List, Tuple


def _split_sentences(text: str) -> List[str]:
    """Split text into sentences on . ! ? boundaries."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if s.strip()]


class LateChunker:

    def __init__(
        self,
        min_chunk_size: int = 150,
        max_chunk_size: int = 1500,
        context_sentences: int = 3,
    ):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.context_sentences = context_sentences

    def chunk_and_select(
        self,
        candidates: List[Tuple[str, float, Dict]],
        question: str,
        top_n: int = 5,
    ) -> List[Dict]:
        """
        Given (artifact_id, score, metadata) candidates and the original question,
        return top_n best chunks with context sentences included.

        Returns list of dicts: {artifact_id, score, snippet, metadata}
        """
        results = []
        for artifact_id, score, meta in candidates:
            text = meta.get("text") or meta.get("content") or meta.get("chunk_text", "")
            if not text:
                results.append({
                    "artifact_id": artifact_id,
                    "score": score,
                    "snippet": "",
                    "metadata": meta,
                })
                continue

            chunk = self._extract_best_chunk(text, question)
            results.append({
                "artifact_id": artifact_id,
                "score": score,
                "snippet": chunk,
                "metadata": meta,
            })

        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_n]

    def _extract_best_chunk(self, text: str, question: str) -> str:
        """Extract the most relevant chunk from text for the given question."""
        if len(text) <= self.max_chunk_size:
            return text[: self.max_chunk_size]

        sentences = _split_sentences(text)
        if not sentences:
            return text[: self.max_chunk_size]

        # Find the sentence most relevant to the question (simple keyword overlap)
        q_words = set(question.lower().split())
        best_idx = 0
        best_overlap = -1
        for i, sent in enumerate(sentences):
            overlap = len(q_words & set(sent.lower().split()))
            if overlap > best_overlap:
                best_overlap = overlap
                best_idx = i

        # Grab context_sentences around best_idx
        start = max(0, best_idx - self.context_sentences)
        end = min(len(sentences), best_idx + self.context_sentences + 1)
        chunk = " ".join(sentences[start:end])

        # Trim to max_chunk_size
        return chunk[: self.max_chunk_size]
