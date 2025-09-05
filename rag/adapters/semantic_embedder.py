# adapters/semantic_embedder.py
"""
Semantic Embedder using Sentence Transformers
Provides meaningful text similarity for RAG retrieval
"""
from __future__ import annotations
from typing import List
import logging
import sys
import os

# Add parent directory to path for config access
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SemanticEmbedder:
    """Semantic text embedder using sentence transformers"""

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize semantic embedder with specified model
        
        Args:
            model_name: Name of the sentence transformer model
        """
        self.model_name = model_name
        self._model = None
        self._dim = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the model immediately to detect errors early"""
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading sentence transformer model: {self.model_name}")
            
            self._model = SentenceTransformer(self.model_name)
            self._dim = self._model.get_sentence_embedding_dimension()
            
            logger.info(f"✅ Model '{self.model_name}' loaded successfully")
            logger.info(f"   Embedding dimension: {self._dim}")
            
        except ImportError:
            error_msg = (
                "CRITICAL ERROR: 'sentence-transformers' library is not installed.\n"
                "This is required for semantic search functionality.\n"
                "Please install it using: pip install sentence-transformers"
            )
            logger.error(error_msg)
            raise RuntimeError("Missing required dependency: sentence-transformers")
            
        except Exception as e:
            error_msg = f"Failed to load model '{self.model_name}': {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def getDim(self) -> int:
        """Get embedding dimension"""
        if self._dim is None:
            raise RuntimeError("Embedder not properly initialized")
        return self._dim

    def embedTexts(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple texts using the sentence transformer model
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors (as lists of floats)
        """
        if not self._model:
            raise RuntimeError("Model not loaded. Cannot perform embedding.")
        
        if not texts:
            return []
        
        try:
            # Encode texts to numpy arrays, then convert to lists
            embeddings = self._model.encode(
                texts, 
                convert_to_tensor=False,
                show_progress_bar=len(texts) > 100,  # Show progress for large batches
                batch_size=32  # Process in batches for efficiency
            )
            
            # Convert numpy arrays to lists for JSON serialization
            return [embedding.tolist() for embedding in embeddings]
            
        except Exception as e:
            logger.error(f"Error during text embedding: {str(e)}")
            raise RuntimeError(f"Embedding failed: {str(e)}")


class EmbedderFactory:
    """Factory for creating embedders based on configuration"""
    
    # Model recommendations for different use cases
    MODELS = {
        # English models
        'english-small': 'all-MiniLM-L6-v2',  # Fast, good quality (384 dims)
        'english-base': 'all-mpnet-base-v2',  # Better quality (768 dims)
        'english-large': 'all-roberta-large-v1',  # Best quality (1024 dims)
        
        # Multilingual models (supports Korean, English, etc.)
        'multilingual-small': 'paraphrase-multilingual-MiniLM-L12-v2',  # Fast (384 dims)
        'multilingual-base': 'paraphrase-multilingual-mpnet-base-v2',  # Better (768 dims)
        
        # Korean-specific models
        'korean': 'jhgan/ko-sroberta-multitask',  # Korean optimized (768 dims)
        
        # Domain-specific
        'qa': 'multi-qa-MiniLM-L6-cos-v1',  # Optimized for Q&A (384 dims)
        'msmarco': 'msmarco-MiniLM-L6-cos-v5',  # Optimized for search (384 dims)
    }
    
    @classmethod
    def create(cls, config: dict) -> SemanticEmbedder:
        """
        Create embedder based on configuration
        
        Args:
            config: Embedder configuration dictionary
            
        Returns:
            Configured SemanticEmbedder instance
        """
        embedder_type = config.get('type', 'semantic')
        
        if embedder_type != 'semantic':
            raise ValueError(
                f"Unsupported embedder type: {embedder_type}. "
                "Only 'semantic' is supported for proper RAG functionality."
            )
        
        # Get model from config or use default
        model_config = config.get('model', 'multilingual-small')
        
        # Check if it's a preset or custom model name
        if model_config in cls.MODELS:
            model_name = cls.MODELS[model_config]
            logger.info(f"Using preset model '{model_config}': {model_name}")
        else:
            # Assume it's a full model name from HuggingFace
            model_name = model_config
            logger.info(f"Using custom model: {model_name}")
        
        return SemanticEmbedder(model_name=model_name)
    
    @classmethod
    def get_model_info(cls) -> dict:
        """Get information about available models"""
        return {
            "presets": cls.MODELS,
            "recommended": {
                "korean_documents": "multilingual-base",
                "english_only": "english-base",
                "fast_prototype": "english-small",
                "qa_system": "qa"
            }
        }
