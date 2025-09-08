# chunkers/sliding_window_chunker.py
from __future__ import annotations
from typing import List, Dict
import sys
sys.path.append('E:/Ragproject/rag')
from rag.core.types import Document, Chunk
from rag.chunkers.base import IChunker, ChunkingParams
from rag.chunkers.utils import create_chunk_meta, generate_chunk_id


class SlidingWindowChunker(IChunker):
    """Sliding window chunker with overlap"""
    
    def chunk(self, doc: Document, params: ChunkingParams) -> List[Chunk]:
        text = doc.text
        if not text:
            return []
        
        chunks = []
        window_size = params.windowSize
        overlap = params.overlap
        step = max(1, window_size - overlap)
        
        idx = 0
        position = 0
        text_length = len(text)
        
        while position < text_length:
            # Calculate end position
            end = min(position + window_size, text_length)
            
            # Extract chunk text
            chunk_text = text[position:end]
            
            # Try to find a good breaking point (sentence or word boundary)
            if end < text_length:
                chunk_text = self._adjust_chunk_boundary(chunk_text, text, position, end)
            
            meta = create_chunk_meta(
                doc,
                chunk_type="sliding_window",
                chunk_index=idx,
                position=position,
                overlap=overlap if position > 0 else 0
            )
            
            chunks.append(
                Chunk(
                    id=generate_chunk_id(doc.id, idx, "sw"),
                    docId=doc.id,
                    text=chunk_text.strip(),
                    meta=meta
                )
            )
            
            # Move to next position
            position += step
            idx += 1
            
            # Break if we've processed the entire text
            if end >= text_length:
                break
        
        return chunks
    
    def _adjust_chunk_boundary(self, chunk_text: str, full_text: str, 
                              start: int, end: int) -> str:
        """Adjust chunk boundary to avoid breaking in the middle of a sentence"""
        # Look for the last sentence ending in the chunk
        last_period = chunk_text.rfind('.')
        last_question = chunk_text.rfind('?')
        last_exclaim = chunk_text.rfind('!')
        
        # Find the last sentence boundary
        last_boundary = max(last_period, last_question, last_exclaim)
        
        if last_boundary > len(chunk_text) * 0.8:  # If boundary is near the end
            return chunk_text[:last_boundary + 1]
        
        # Otherwise, look for a word boundary
        last_space = chunk_text.rfind(' ')
        if last_space > len(chunk_text) * 0.9:
            return chunk_text[:last_space]
        
        return chunk_text
    
    def name(self) -> str:
        return "sliding_window"
    
    def description(self) -> str:
        return "Fixed-size chunks with configurable overlap to preserve context"
