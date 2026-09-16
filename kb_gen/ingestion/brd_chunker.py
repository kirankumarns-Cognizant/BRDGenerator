"""
BRDChunker — splits BRD text into overlapping chunks by heading structure.
Parameters:
  max_chars (default 1400)
  overlap_chars (default 180)
  max_chunks (default 5000)
  min_per_document: minimum chunks to always produce (default 1)
"""
import re
from typing import List


class BRDChunker:

    def __init__(
        self,
        max_chars: int = 1400,
        overlap_chars: int = 180,
        max_chunks: int = 5000,
        min_per_document: int = 1,
    ):
        self.max_chars = max_chars
        self.overlap_chars = overlap_chars
        self.max_chunks = max_chunks
        self.min_per_document = min_per_document

    def chunk(self, text: str, artifact_id: str = "") -> List[dict]:
        """
        Split text into overlapping chunks.
        Returns list of dicts: {chunk_id, text, char_start, char_end, heading}
        """
        if not text or not text.strip():
            return []

        sections = self._split_by_headings(text)
        chunks = []

        for heading, section_text in sections:
            section_chunks = self._chunk_section(section_text, heading)
            chunks.extend(section_chunks)

        # Apply overlap between adjacent chunks
        overlapping = self._apply_overlap(chunks)

        # Trim to max_chunks
        overlapping = overlapping[: self.max_chunks]

        # Ensure at least min_per_document
        if not overlapping and text.strip():
            overlapping = [{
                "chunk_id": f"{artifact_id}_chunk_0" if artifact_id else "chunk_0",
                "text": text[: self.max_chars],
                "char_start": 0,
                "char_end": min(len(text), self.max_chars),
                "heading": "",
            }]

        # Assign IDs
        for i, chunk in enumerate(overlapping):
            chunk["chunk_id"] = f"{artifact_id}_chunk_{i}" if artifact_id else f"chunk_{i}"

        return overlapping

    def _split_by_headings(self, text: str) -> List[tuple]:
        """Split text on markdown headings (# ## ###)."""
        pattern = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
        matches = list(pattern.finditer(text))

        if not matches:
            return [("", text)]

        sections = []
        for i, match in enumerate(matches):
            heading = match.group(2).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            section_text = text[start:end].strip()
            if section_text:
                sections.append((heading, section_text))

        # Text before first heading
        before = text[: matches[0].start()].strip()
        if before:
            sections.insert(0, ("", before))

        return sections or [("", text)]

    def _chunk_section(self, text: str, heading: str) -> List[dict]:
        """Split a section into max_chars chunks."""
        if len(text) <= self.max_chars:
            return [{"text": text, "heading": heading, "char_start": 0, "char_end": len(text)}]

        chunks = []
        pos = 0
        while pos < len(text):
            end = min(pos + self.max_chars, len(text))
            # Try to break on a sentence boundary
            chunk_text = text[pos:end]
            if end < len(text):
                last_period = chunk_text.rfind(". ")
                if last_period > self.max_chars // 2:
                    end = pos + last_period + 2
                    chunk_text = text[pos:end]
            chunks.append({
                "text": chunk_text.strip(),
                "heading": heading,
                "char_start": pos,
                "char_end": end,
            })
            pos = end
        return chunks

    def _apply_overlap(self, chunks: List[dict]) -> List[dict]:
        """Prepend overlap_chars from the previous chunk to each chunk."""
        result = []
        for i, chunk in enumerate(chunks):
            if i == 0 or not self.overlap_chars:
                result.append(chunk)
            else:
                prev_text = chunks[i - 1]["text"]
                overlap = prev_text[-self.overlap_chars:].strip()
                chunk = dict(chunk)
                chunk["text"] = overlap + " " + chunk["text"]
                result.append(chunk)
        return result
