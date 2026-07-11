from __future__ import annotations

import re
import uuid
from typing import Any

from domains.rag.models import Document, DocumentChunk


class ChunkingService:
    """Splits documents into chunks using configurable strategies."""

    def __init__(self, default_chunk_size: int = 512, default_overlap: int = 128):
        self.default_chunk_size = default_chunk_size
        self.default_overlap = default_overlap

    def chunk_document(
        self,
        document: Document,
        strategy: str = "hybrid",
        chunk_size: int | None = None,
        overlap: int | None = None,
    ) -> list[DocumentChunk]:
        chunk_size = chunk_size or self.default_chunk_size
        overlap = overlap or self.default_overlap

        if strategy == "fixed_size":
            return self._chunk_fixed_size(document, chunk_size, overlap)
        elif strategy == "semantic":
            return self._chunk_semantic(document, chunk_size, overlap)
        elif strategy == "hybrid":
            return self._chunk_hybrid(document, chunk_size, overlap)
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")

    def _chunk_fixed_size(
        self, document: Document, chunk_size: int, overlap: int
    ) -> list[DocumentChunk]:
        tokens = self._tokenize(document.content)
        chunks: list[DocumentChunk] = []
        start = 0
        index = 0

        while start < len(tokens):
            end = min(start + chunk_size, len(tokens))
            chunk_text = self._detokenize(tokens[start:end])
            chunks.append(
                DocumentChunk(
                    id=str(uuid.uuid4()),
                    document_id=document.id,
                    content=chunk_text,
                    chunk_index=index,
                    metadata={"strategy": "fixed_size", "start_token": start, "end_token": end},
                )
            )
            index += 1
            if end == len(tokens):
                break
            start += chunk_size - overlap

        return chunks

    def _chunk_semantic(
        self, document: Document, chunk_size: int, overlap: int
    ) -> list[DocumentChunk]:
        sections = self._split_by_semantic_boundaries(document.content)
        chunks: list[DocumentChunk] = []
        buffer: list[str] = []
        buffer_len = 0
        index = 0

        for section in sections:
            section_tokens = self._tokenize(section)
            section_len = len(section_tokens)

            if buffer_len + section_len <= chunk_size:
                buffer.append(section)
                buffer_len += section_len
            else:
                if buffer:
                    chunks.append(self._make_chunk(document, buffer, index, "semantic"))
                    index += 1
                # handle large sections that exceed chunk_size
                if section_len > chunk_size:
                    sub_chunks = self._split_large_section(document, section, chunk_size, overlap, index)
                    chunks.extend(sub_chunks)
                    index += len(sub_chunks)
                    buffer = []
                    buffer_len = 0
                else:
                    buffer = [section]
                    buffer_len = section_len

        if buffer:
            chunks.append(self._make_chunk(document, buffer, index, "semantic"))

        return chunks

    def _chunk_hybrid(
        self, document: Document, chunk_size: int, overlap: int
    ) -> list[DocumentChunk]:
        semantic_chunks = self._chunk_semantic(document, chunk_size, overlap)
        if len(semantic_chunks) <= 1:
            return semantic_chunks

        hybrid: list[DocumentChunk] = []
        buffer: list[str] = []
        buffer_tokens = 0
        index = 0

        for sc in semantic_chunks:
            ct = self._tokenize(sc.content)
            tc = len(ct)

            if buffer_tokens + tc <= chunk_size:
                buffer.append(sc.content)
                buffer_tokens += tc
            else:
                if buffer:
                    hybrid.append(self._make_chunk(document, buffer, index, "hybrid"))
                    index += 1
                buffer = [sc.content]
                buffer_tokens = tc

        if buffer:
            hybrid.append(self._make_chunk(document, buffer, index, "hybrid"))

        return hybrid

    def _split_large_section(
        self, document: Document, section: str, chunk_size: int, overlap: int, start_index: int
    ) -> list[DocumentChunk]:
        tokens = self._tokenize(section)
        chunks: list[DocumentChunk] = []
        start = 0
        idx = start_index

        while start < len(tokens):
            end = min(start + chunk_size, len(tokens))
            chunk_text = self._detokenize(tokens[start:end])
            chunks.append(
                DocumentChunk(
                    id=str(uuid.uuid4()),
                    document_id=document.id,
                    content=chunk_text,
                    chunk_index=idx,
                    metadata={"strategy": "semantic_overflow", "start_token": start, "end_token": end},
                )
            )
            idx += 1
            if end == len(tokens):
                break
            start += chunk_size - overlap

        return chunks

    def _make_chunk(
        self, document: Document, parts: list[str], index: int, strategy: str
    ) -> DocumentChunk:
        return DocumentChunk(
            id=str(uuid.uuid4()),
            document_id=document.id,
            content="\n\n".join(parts),
            chunk_index=index,
            metadata={"strategy": strategy},
        )

    def _split_by_semantic_boundaries(self, text: str) -> list[str]:
        sections = re.split(r"\n\s*\n", text)
        result = []
        for s in sections:
            s = s.strip()
            if s:
                result.append(s)
        if not result:
            result = [text]
        return result

    def _tokenize(self, text: str) -> list[str]:
        if not text:
            return []
        has_arabic = bool(re.search(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]", text))
        if has_arabic:
            return self._tokenize_arabic(text)
        return text.split()

    def _tokenize_arabic(self, text: str) -> list[str]:
        tokens: list[str] = []
        for word in text.split():
            word = word.strip()
            if not word:
                continue
            if len(word) > 20:
                for i in range(0, len(word), 20):
                    tokens.append(word[i : i + 20])
            else:
                tokens.append(word)
        return tokens

    def _detokenize(self, tokens: list[str]) -> str:
        return " ".join(tokens)
