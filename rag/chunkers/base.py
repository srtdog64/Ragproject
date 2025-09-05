# chunkers/base.py
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass
import sys
sys.path.append('E:/Ragproject/rag')
from core.types import Document, Chunk


@dataclass
class ChunkingParams:
    """Chunking parameters"""
    maxTokens: int = 512
    windowSize: int = 1200
    overlap: int = 200
    semanticThreshold: float = 0.82
    language: str = "ko"
    sentenceMinLen: int = 10
    paragraphMinLen: int = 50


class IChunker(ABC):
    """Base interface for all chunking strategies"""
    
    @abstractmethod
    def chunk(self, doc: Document, params: ChunkingParams) -> List[Chunk]:
        """Chunk a document into smaller pieces"""
        pass
    
    @abstractmethod
    def name(self) -> str:
        """Return the name of this chunking strategy"""
        pass
    
    @abstractmethod
    def description(self) -> str:
        """Return a description of this strategy"""
        pass
