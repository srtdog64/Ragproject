# adapters/embedders/adapter.py
"""
Adapter for backward compatibility with existing codebase
Provides the same interface as the original semantic_embedder.py
"""
from __future__ import annotations
from typing import List, Optional
import logging
from .manager import EmbedderManager
from .base import IEmbedder

logger = logging.getLogger(__name__)

class ManagedSemanticEmbedder:
    """
    Backward-compatible wrapper that uses EmbedderManager internally
    but maintains the same interface as the original SemanticEmbedder
    """
    
    def __init__(self, model_name: Optional[str] = None, config_path: str = "config/embeddings.yml"):
        """
        Initialize with optional model name override
        
        Args:
            model_name: Optional specific model/profile to use
            config_path: Path to embeddings YAML config
        """
        self._manager = EmbedderManager.fromYaml(config_path)
        self._profile_name = model_name
        self._embedder: Optional[IEmbedder] = None
        self._signature: Optional[str] = None
        
    def _ensure_embedder(self, texts: List[str] = None):
        """Lazy load embedder based on texts or profile"""
        if self._embedder is None:
            sample_texts = texts or []
            self._embedder, self._signature = self._manager.resolve(
                self._profile_name, 
                sample_texts
            )
            logger.info(f"Using embedder: {self._embedder.getName()} (signature: {self._signature})")
    
    def getDim(self) -> int:
        """Get embedding dimension"""
        self._ensure_embedder()
        return self._embedder.getDim()
    
    def embedTexts(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        # Use the texts to determine best embedder if auto mode
        self._ensure_embedder(texts)
        return self._embedder.embedTexts(texts)
    
    def getNamespace(self) -> str:
        """Get namespace for vector storage"""
        if self._signature:
            return self._manager.namespaceFor(self._signature)
        return "default"

# For complete backward compatibility
SemanticEmbedder = ManagedSemanticEmbedder
