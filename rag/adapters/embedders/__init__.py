# adapters/embedders/__init__.py
from .base import IEmbedder, Result, FallbackEmbedder
from .sentence_transformers_embedder import SentenceTransformersEmbedder
from .manager import EmbedderManager, EmbedderProfile, EmbedderPolicy

__all__ = [
    'IEmbedder',
    'Result',
    'FallbackEmbedder',
    'SentenceTransformersEmbedder',
    'EmbedderManager',
    'EmbedderProfile',
    'EmbedderPolicy'
]
