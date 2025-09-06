# rerankers/factory.py
"""
Factory for creating reranker instances based on configuration
"""
import logging
from core.interfaces import Reranker
from rerankers.identity_reranker import IdentityReranker
from rerankers.cross_encoder_reranker import CrossEncoderReranker, SimpleScoreReranker

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
            reranker_type: Type of reranker ('identity', 'cross-encoder', 'simple')
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
        
        else:
            # Default to identity (no reranking)
            if reranker_type != "identity":
                logger.warning(f"Unknown reranker type '{reranker_type}', using IdentityReranker")
            return IdentityReranker()
