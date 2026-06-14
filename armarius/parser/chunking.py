"""Text chunking strategies for preserving bounding box information."""

from typing import List
from armarius.parser.pdf_parser import TextChunk, BoundingBox


class ChunkStrategy:
    """Base class for text chunking strategies."""

    def chunk(self, chunks: List[TextChunk]) -> List[TextChunk]:
        raise NotImplementedError


class BlockLevelChunking(ChunkStrategy):
    """Keep PDF blocks as-is (default PyMuPDF behavior)."""

    def chunk(self, chunks: List[TextChunk]) -> List[TextChunk]:
        return chunks


class SentenceLevelChunking(ChunkStrategy):
    """Split blocks into sentences, merging bboxes."""

    def __init__(self, max_chars: int = 500):
        self.max_chars = max_chars

    def chunk(self, chunks: List[TextChunk]) -> List[TextChunk]:
        result = []
        for chunk in chunks:
            sentences = self._split_sentences(chunk.text)
            
            current_text = ""
            start_idx = 0
            
            for sentence in sentences:
                if len(current_text) + len(sentence) > self.max_chars and current_text:
                    new_chunk = TextChunk(
                        text=current_text.strip(),
                        bbox=chunk.bbox,
                        pdf_path=chunk.pdf_path,
                    )
                    result.append(new_chunk)
                    current_text = sentence
                else:
                    current_text += " " + sentence if current_text else sentence
            
            if current_text:
                new_chunk = TextChunk(
                    text=current_text.strip(),
                    bbox=chunk.bbox,
                    pdf_path=chunk.pdf_path,
                )
                result.append(new_chunk)
        
        return result

    def _split_sentences(self, text: str) -> List[str]:
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]


class FixedSizeChunking(ChunkStrategy):
    """Fixed-size chunks with overlap, preserving bbox."""

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, chunks: List[TextChunk]) -> List[TextChunk]:
        result = []
        for chunk in chunks:
            text = chunk.text
            start = 0
            
            while start < len(text):
                end = start + self.chunk_size
                chunk_text = text[start:end]
                
                new_chunk = TextChunk(
                    text=chunk_text.strip(),
                    bbox=chunk.bbox,
                    pdf_path=chunk.pdf_path,
                )
                result.append(new_chunk)
                
                start = end - self.overlap
        
        return result
