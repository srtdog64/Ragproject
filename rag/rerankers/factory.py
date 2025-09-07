# rerankers/factory.py
"""
Factory for creating reranker instances based on configuration
"""
import logging
from core.interfaces import Reranker
from rerankers.identity_reranker import IdentityReranker
from rerankers.cross_encoder_reranker import CrossEncoderReranker, SimpleScoreReranker
from rerankers.bm25_reranker import BM25Reranker
from rerankers.hybrid_reranker import HybridReranker

try:
    from rerankers.cohere_reranker import CohereReranker
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False

logger = logging.getLogger(__name__)

class RerankerFactory:
    """
    Factory class for creating reranker instances
    """
    
    @staticmethod
    def create(reranker_type: str = "identity", **kwargs) -> Reranker:
        """
        Create a reranker instance based on type
        
        Args:
            reranker_type: Type of reranker
            **kwargs: Additional arguments for the specific reranker
        
        Returns:
            Reranker instance
        """
        logger.info(f"Creating reranker of type: {reranker_type}")
        
        if reranker_type == "cross-encoder":
            # Cross-encoder based reranking
            model_name = kwargs.get('model', 'cross-encoder/ms-marco-MiniLM-L-6-v2')
            device = kwargs.get('device', 'cpu')
            try:
                return CrossEncoderReranker(
                    model_name=model_name,
                    device=device
                )
            except Exception as e:
                logger.error(f"Failed to create CrossEncoderReranker: {e}")
                logger.warning("Falling back to SimpleScoreReranker")
                return SimpleScoreReranker()
        
        elif reranker_type == "simple":
            # Simple score-based reranking
            return SimpleScoreReranker(
                boost_recent=kwargs.get('boost_recent', True),
                boost_title_match=kwargs.get('boost_title_match', True)
            )
        
        elif reranker_type == "bm25":
            # BM25 reranking
            return BM25Reranker(
                k1=kwargs.get('k1', 1.2),
                b=kwargs.get('b', 0.75)
            )
        
        elif reranker_type == "hybrid":
            # Hybrid reranking
            weights = kwargs.get('weights', {
                'semantic': 0.5,
                'bm25': 0.3,
                'simple': 0.2
            })
            return HybridReranker(weights=weights)
        
        elif reranker_type == "cohere":
            # Cohere API reranking
            if not COHERE_AVAILABLE:
                logger.error("Cohere not available, falling back to simple reranker")
                return SimpleScoreReranker()
            
            try:
                return CohereReranker(
                    api_key=kwargs.get('api_key'),
                    model=kwargs.get('model', 'rerank-english-v2.0')
                )
            except Exception as e:
                logger.error(f"Failed to create CohereReranker: {e}")
                return SimpleScoreReranker()
        
        else:
            # Default to identity (no reranking)
            if reranker_type != "identity":
                logger.warning(f"Unknown reranker type '{reranker_type}', using IdentityReranker")
            return IdentityReranker()
