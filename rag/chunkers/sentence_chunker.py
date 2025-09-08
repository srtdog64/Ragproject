# chunkers/sentence_chunker.py
from __future__ import annotations
from typing import List, Dict
import re
import sys
sys.path.append('E:/Ragproject/rag')
from rag.core.types import Document, Chunk
from rag.chunkers.base import IChunker, ChunkingParams
from rag.chunkers.utils import create_chunk_meta, generate_chunk_id


class SentenceChunker(IChunker):
    """Chunk by sentence boundaries"""
    
    def chunk(self, doc: Document, params: ChunkingParams) -> List[Chunk]:
        text = doc.text
        if not text:
            return []
        
        # Korean and English sentence splitters
        sentences = self._split_sentences(text, params.language)
        
        chunks = []
        for idx, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if len(sentence) < params.sentenceMinLen:
                continue
                
            # Use helper function for metadata
            meta = create_chunk_meta(
                doc, 
                chunk_type="sentence",
                chunk_index=idx,
                sentence_length=len(sentence)
            )
            chunks.append(
                Chunk(
                    id=f"{doc.id}:sent_{idx}",
                    docId=doc.id,
                    text=sentence,
                    meta=meta
                )
            )
        
        return chunks
    
    def _split_sentences(self, text: str, language: str) -> List[str]:
        """Split text into sentences based on language"""
        if language == "ko":
            # Korean sentence endings: 다, 요, 까, 죠, etc + punctuation
            pattern = r'[.!?。！？]\s*|\n\n+'
        else:
            # English sentence endings
            pattern = r'[.!?]\s+|\n\n+'
        
        sentences = re.split(pattern, text)
        # Filter out empty strings
        return [s for s in sentences if s.strip()]
    
    def name(self) -> str:
        return "sentence"
    
    def description(self) -> str:
        return "Split text by sentence boundaries, preserving complete semantic units"
