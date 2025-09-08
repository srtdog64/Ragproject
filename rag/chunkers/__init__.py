# chunkers/__init__.py
# Simple imports without dependencies between modules

__all__ = [
    'IChunker',
    'ChunkingParams', 
    'SentenceChunker',
    'ParagraphChunker',
    'SlidingWindowChunker',
    'AdaptiveChunker',
    'SimpleOverlapChunker',
    'ChunkerRegistry',
    'registry'
]

# Lazy imports to avoid circular dependencies
def __getattr__(name):
    if name == 'IChunker':
        from rag.chunkers.base import IChunker
        return IChunker
    elif name == 'ChunkingParams':
        from rag.chunkers.base import ChunkingParams
        return ChunkingParams
    elif name == 'SentenceChunker':
        from rag.chunkers.sentence_chunker import SentenceChunker
        return SentenceChunker
    elif name == 'ParagraphChunker':
        from rag.chunkers.paragraph_chunker import ParagraphChunker
        return ParagraphChunker
    elif name == 'SlidingWindowChunker':
        from rag.chunkers.sliding_window_chunker import SlidingWindowChunker
        return SlidingWindowChunker
    elif name == 'AdaptiveChunker':
        from rag.chunkers.adaptive_chunker import AdaptiveChunker
        return AdaptiveChunker
    elif name == 'SimpleOverlapChunker':
        from rag.chunkers.overlap_chunker import SimpleOverlapChunker
        return SimpleOverlapChunker
    elif name == 'ChunkerRegistry':
        from rag.chunkers.registry import ChunkerRegistry
        return ChunkerRegistry
    elif name == 'registry':
        from rag.chunkers.registry import registry
        return registry
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
