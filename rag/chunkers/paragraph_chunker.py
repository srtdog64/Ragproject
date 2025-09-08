# chunkers/paragraph_chunker.py
from __future__ import annotations
from typing import List, Dict
import re
import sys
sys.path.append('E:/Ragproject/rag')
from rag.core.types import Document, Chunk
from rag.chunkers.base import IChunker, ChunkingParams
from rag.chunkers.utils import create_chunk_meta, generate_chunk_id


class ParagraphChunker(IChunker):
    """Chunk by paragraph boundaries"""
    
    def chunk(self, doc: Document, params: ChunkingParams) -> List[Chunk]:
        text = doc.text
        if not text:
            return []
        
        # Split by double newlines or multiple spaces (paragraph boundaries)
        paragraphs = re.split(r'\n\s*\n+|\r\n\s*\r\n+', text)
        
        chunks = []
        for idx, paragraph in enumerate(paragraphs):
            paragraph = paragraph.strip()
            if len(paragraph) < params.paragraphMinLen:
                continue
            
            # If paragraph is too long, it might need further splitting
            if len(paragraph) > params.maxTokens * 4:  # rough estimate
                # Split long paragraphs by sentence
                sub_chunks = self._split_long_paragraph(
                    paragraph, doc, idx, params
                )
                chunks.extend(sub_chunks)
            else:
                meta = create_chunk_meta(
                    doc,
                    chunk_type="paragraph",
                    chunk_index=idx
                )
                chunks.append(
                    Chunk(
                        id=generate_chunk_id(doc.id, idx, "para"),
                        docId=doc.id,
                        text=paragraph,
                        meta=meta
                    )
                )
        
        return chunks
    
    def _split_long_paragraph(self, paragraph: str, doc: Document, 
                             para_idx: int, params: ChunkingParams) -> List[Chunk]:
        """Split a long paragraph into smaller chunks"""
        chunks = []
        sentences = re.split(r'[.!?]\s+', paragraph)
        
        current_chunk = ""
        sub_idx = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Add period back if missing
            if not sentence.endswith(('.', '!', '?')):
                sentence += '.'
            
            if len(current_chunk) + len(sentence) < params.windowSize:
                current_chunk += " " + sentence if current_chunk else sentence
            else:
                if current_chunk:
                    meta = create_chunk_meta(
                        doc,
                        chunk_type="paragraph_split",
                        chunk_index=para_idx,
                        sub_index=sub_idx
                    )
                    chunks.append(
                        Chunk(
                            id=f"{doc.id}:para_{para_idx}_{sub_idx}",
                            docId=doc.id,
                            text=current_chunk.strip(),
                            meta=meta
                        )
                    )
                    sub_idx += 1
                current_chunk = sentence
        
        # Add the last chunk
        if current_chunk:
            meta = create_chunk_meta(
                doc,
                chunk_type="paragraph_split",
                chunk_index=para_idx,
                sub_index=sub_idx
            )
            chunks.append(
                Chunk(
                    id=f"{doc.id}:para_{para_idx}_{sub_idx}",
                    docId=doc.id,
                    text=current_chunk.strip(),
                    meta=meta
                )
            )
        
        return chunks
    
    def name(self) -> str:
        return "paragraph"
    
    def description(self) -> str:
        return "Split text by paragraph boundaries, ideal for structured documents"
