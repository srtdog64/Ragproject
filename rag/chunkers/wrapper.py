# chunkers/wrapper.py
"""
Wrapper to make new chunkers compatible with the old interface
"""
from __future__ import annotations
from typing import List
import sys
sys.path.append('E:/Ragproject/rag')
from core.types import Document, Chunk
from core.interfaces import Chunker
from chunkers.base import IChunker, ChunkingParams
from chunkers.registry import registry


class ChunkerWrapper:
    """Wrapper class to make IChunker compatible with the old Chunker protocol"""
    
    def __init__(self):
        """Initialize with registry"""
        self.registry = registry
    
    def chunk(self, doc: Document) -> List[Chunk]:
        """
        Chunk a document using the current strategy from registry
        This method is compatible with the old Chunker protocol
        """
        # Get current chunker and params from registry
        chunker = self.registry.get_chunker()
        params = self.registry.get_params()
        
        # If it's an old-style chunker (has the old chunk signature)
        # check if it needs params
        import inspect
        sig = inspect.signature(chunker.chunk)
        param_names = list(sig.parameters.keys())
        
        if len(param_names) == 1 or (len(param_names) == 2 and 'params' not in param_names[1]):
            # Old style chunker - just pass doc
            return chunker.chunk(doc)
        else:
            # New style chunker - pass both doc and params
            return chunker.chunk(doc, params)


class OldStyleChunkerAdapter:
    """Adapter to make old chunkers work with new interface"""
    
    def __init__(self, old_chunker):
        self.old_chunker = old_chunker
    
    def chunk(self, doc: Document, params: ChunkingParams = None) -> List[Chunk]:
        """Adapt old chunk method to new signature"""
        # Old chunkers don't use params, just call with doc
        return self.old_chunker.chunk(doc)
    
    def name(self) -> str:
        """Return name if available"""
        if hasattr(self.old_chunker, 'name'):
            return self.old_chunker.name()
        return self.old_chunker.__class__.__name__
    
    def description(self) -> str:
        """Return description if available"""
        if hasattr(self.old_chunker, 'description'):
            return self.old_chunker.description()
        return f"Legacy chunker: {self.name()}"
