# chunkers/adaptive_chunker.py
from __future__ import annotations
from typing import List, Dict
import re
import sys
sys.path.append('E:/Ragproject/rag')
from rag.core.types import Document, Chunk
from rag.chunkers.base import IChunker, ChunkingParams
from chunkers.paragraph_chunker import ParagraphChunker
from chunkers.sentence_chunker import SentenceChunker
from rag.chunkers.utils import create_chunk_meta


class AdaptiveChunker(IChunker):
    """Adaptive chunking based on content characteristics"""
    
    def __init__(self):
        self.paragraph_chunker = ParagraphChunker()
        self.sentence_chunker = SentenceChunker()
    
    def chunk(self, doc: Document, params: ChunkingParams) -> List[Chunk]:
        text = doc.text
        if not text:
            return []
        
        # Analyze document characteristics
        stats = self._analyze_text(text)
        
        # Choose strategy based on analysis
        if stats['is_structured']:
            # Use paragraph chunking for structured documents
            chunks = self.paragraph_chunker.chunk(doc, params)
        elif stats['avg_sentence_length'] < 50:
            # Short sentences - use sentence chunking
            chunks = self.sentence_chunker.chunk(doc, params)
        else:
            # Mixed approach
            chunks = self._mixed_chunking(doc, params, stats)
        
        # Post-process to ensure chunks are within token limits
        chunks = self._adjust_chunk_sizes(chunks, params)
        
        return chunks
    
    def _analyze_text(self, text: str) -> Dict:
        """Analyze text characteristics"""
        lines = text.split('\n')
        sentences = re.split(r'[.!?]\s+', text)
        
        # Check for structure indicators
        has_headers = any(line.startswith('#') for line in lines)
        has_lists = any(line.strip().startswith(('-', '*', '1.')) for line in lines)
        double_newlines = text.count('\n\n')
        
        # Calculate statistics
        avg_sentence_length = sum(len(s) for s in sentences) / max(1, len(sentences))
        punctuation_density = sum(1 for c in text if c in '.!?,;:') / max(1, len(text)) * 1000
        
        return {
            'is_structured': has_headers or has_lists or double_newlines > 5,
            'avg_sentence_length': avg_sentence_length,
            'punctuation_density': punctuation_density,
            'line_count': len(lines),
            'sentence_count': len(sentences),
            'total_length': len(text)
        }
    
    def _mixed_chunking(self, doc: Document, params: ChunkingParams, 
                       stats: Dict) -> List[Chunk]:
        """Apply mixed chunking strategy"""
        text = doc.text
        chunks = []
        
        # Split into sections first
        sections = re.split(r'\n\s*\n+', text)
        
        for section_idx, section in enumerate(sections):
            section = section.strip()
            if not section:
                continue
            
            # For long sections, apply sliding window
            if len(section) > params.windowSize:
                chunks.extend(self._sliding_window_section(
                    section, doc, section_idx, params
                ))
            else:
                # For shorter sections, keep as single chunk
                meta = {
                    "title": doc.title,
                    "source": doc.source,
                    "chunk_type": "adaptive_section"
                }
                chunks.append(
                    Chunk(
                        id=f"{doc.id}:adapt_{section_idx}",
                        docId=doc.id,
                        text=section,
                        meta=meta
                    )
                )
        
        return chunks
    
    def _sliding_window_section(self, section: str, doc: Document,
                               section_idx: int, params: ChunkingParams) -> List[Chunk]:
        """Apply sliding window to a section"""
        chunks = []
        window_size = params.windowSize
        overlap = params.overlap
        step = max(1, window_size - overlap)
        
        position = 0
        sub_idx = 0
        
        while position < len(section):
            end = min(position + window_size, len(section))
            chunk_text = section[position:end].strip()
            
            if chunk_text:
                meta = {
                    "title": doc.title,
                    "source": doc.source,
                    "chunk_type": "adaptive_window",
                    "section": section_idx
                }
                chunks.append(
                    Chunk(
                        id=f"{doc.id}:adapt_{section_idx}_{sub_idx}",
                        docId=doc.id,
                        text=chunk_text,
                        meta=meta
                    )
                )
                sub_idx += 1
            
            position += step
            
            if end >= len(section):
                break
        
        return chunks
    
    def _adjust_chunk_sizes(self, chunks: List[Chunk], 
                           params: ChunkingParams) -> List[Chunk]:
        """Ensure chunks are within size limits"""
        adjusted = []
        max_size = params.maxTokens * 4  # Rough char estimate
        
        for chunk in chunks:
            if len(chunk.text) > max_size:
                # Split oversized chunks
                text = chunk.text
                position = 0
                sub_idx = 0
                
                while position < len(text):
                    end = min(position + max_size, len(text))
                    sub_text = text[position:end].strip()
                    
                    if sub_text:
                        new_meta = dict(chunk.meta)
                        new_meta['split'] = True
                        adjusted.append(
                            Chunk(
                                id=f"{chunk.id}_split_{sub_idx}",
                                docId=chunk.docId,
                                text=sub_text,
                                meta=new_meta
                            )
                        )
                        sub_idx += 1
                    
                    position = end
            else:
                adjusted.append(chunk)
        
        return adjusted
    
    def name(self) -> str:
        return "adaptive"
    
    def description(self) -> str:
        return "Adaptive strategy that chooses the best approach based on content analysis"
