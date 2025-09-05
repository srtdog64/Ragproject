# chunkers/overlap_chunker.py
from __future__ import annotations
from typing import List, Dict
import sys
sys.path.append('E:/Ragproject/rag')
from core.types import Document, Chunk
from chunkers.base import IChunker, ChunkingParams

class SimpleOverlapChunker(IChunker):
    def __init__(self, size: int = 800, overlap: int = 120):
        self._size = max(200, size)
        self._overlap = max(0, overlap)

    def getSize(self) -> int:
        return self._size

    def setSize(self, s: int) -> None:
        self._size = max(200, s)

    def getOverlap(self) -> int:
        return self._overlap

    def setOverlap(self, o: int) -> None:
        self._overlap = max(0, o)
    
    def name(self) -> str:
        return "simple_overlap"
    
    def description(self) -> str:
        return "Simple overlapping chunks with fixed size"

    def chunk(self, doc: Document, params: ChunkingParams = None) -> List[Chunk]:
        # Use instance values or params if provided
        if params:
            self._size = params.windowSize
            self._overlap = params.overlap
        text = doc.text
        if len(text) == 0:
            return []
        chunks: List[Chunk] = []
        start = 0
        idx = 0
        while start < len(text):
            end = min(len(text), start + self._size)
            window = text[start:end]
            meta: Dict[str, str] = {"title": doc.title, "source": doc.source}
            chunks.append(Chunk(id=f"{doc.id}:{idx}", docId=doc.id, text=window, meta=meta))
            if end >= len(text):
                break
            start = end - self._overlap
            idx += 1
        return chunks
