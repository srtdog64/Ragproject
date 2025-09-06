# stores/namespace_manager.py
"""
Namespace management for embedding model-specific collections
"""
import hashlib
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class NamespaceManager:
    """
    Manages namespaces for different embedding models
    Allows switching between models without losing indexed data
    """
    
    def __init__(self, base_collection_name: str = "rag_documents"):
        self.base_name = base_collection_name
        self.current_namespace = None
        self.namespaces_cache = {}
    
    def get_namespace_for_model(self, model_name: str, model_dim: int = None) -> str:
        """
        Generate a unique namespace for an embedding model
        
        Args:
            model_name: Name of the embedding model
            model_dim: Dimension of embeddings (optional)
            
        Returns:
            Unique namespace string
        """
        # Create a signature from model properties
        signature_parts = [model_name]
        if model_dim:
            signature_parts.append(str(model_dim))
        
        signature = "_".join(signature_parts)
        # Create a short hash for the signature
        hash_sig = hashlib.md5(signature.encode()).hexdigest()[:8]
        
        # Format: base_modelname_hash
        # Example: rag_documents_multilingual_minilm_a1b2c3d4
        safe_model_name = model_name.replace("/", "_").replace("-", "_").lower()
        # Truncate model name if too long
        if len(safe_model_name) > 30:
            safe_model_name = safe_model_name[:30]
        
        namespace = f"{self.base_name}_{safe_model_name}_{hash_sig}"
        
        logger.info(f"Generated namespace: {namespace} for model: {model_name}")
        return namespace
    
    def list_available_namespaces(self, chroma_client) -> List[Dict[str, Any]]:
        """
        List all available namespaces (collections) with their metadata
        
        Args:
            chroma_client: ChromaDB client instance
            
        Returns:
            List of namespace information
        """
        namespaces = []
        
        try:
            collections = chroma_client.list_collections()
            
            for collection in collections:
                if collection.name.startswith(self.base_name):
                    # Parse namespace to extract model info
                    parts = collection.name.split("_")
                    
                    # Get collection metadata
                    try:
                        count = collection.count()
                    except:
                        count = 0
                    
                    namespace_info = {
                        "name": collection.name,
                        "count": count,
                        "model": self._extract_model_from_namespace(collection.name)
                    }
                    
                    namespaces.append(namespace_info)
            
        except Exception as e:
            logger.error(f"Failed to list namespaces: {e}")
        
        return namespaces
    
    def _extract_model_from_namespace(self, namespace: str) -> str:
        """
        Extract model name from namespace
        
        Args:
            namespace: Namespace string
            
        Returns:
            Model name or "unknown"
        """
        if not namespace.startswith(self.base_name):
            return "unknown"
        
        # Remove base name and hash
        parts = namespace[len(self.base_name) + 1:].rsplit("_", 1)
        if parts:
            return parts[0].replace("_", "-")
        return "unknown"
    
    def switch_namespace(self, namespace: str):
        """
        Switch to a different namespace
        
        Args:
            namespace: Target namespace
        """
        self.current_namespace = namespace
        logger.info(f"Switched to namespace: {namespace}")
    
    def get_current_namespace(self) -> Optional[str]:
        """Get the current active namespace"""
        return self.current_namespace
    
    def create_namespace_metadata(self, model_name: str, model_dim: int,
                                 model_type: str = None) -> Dict[str, Any]:
        """
        Create metadata for a namespace
        
        Args:
            model_name: Embedding model name
            model_dim: Embedding dimension
            model_type: Type of model (sentence-transformers, openai, etc.)
            
        Returns:
            Metadata dictionary
        """
        from datetime import datetime
        
        return {
            "model_name": model_name,
            "model_dim": model_dim,
            "model_type": model_type or "sentence-transformers",
            "created_at": datetime.now().isoformat(),
            "base_collection": self.base_name
        }
