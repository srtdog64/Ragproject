# rerankers/cross_encoder_reranker.py
"""
Cross-encoder based reranker using sentence transformers
"""
import logging
from typing import List
from core.interfaces import Reranker
from core.types import Retrieved
from dataclasses import replace
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CROSS_ENCODER_AVAILABLE = False
    logger.warning("sentence-transformers not installed for CrossEncoder")


class CrossEncoderReranker(Reranker):
    """
    Cross-encoder based reranker for high-quality semantic reranking
    """
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2", device: str = "cpu"):
        """
        Initialize cross-encoder reranker
        
        Args:
            model_name: Name of the cross-encoder model
            device: Device to run on (cpu/cuda)
        """
        if not CROSS_ENCODER_AVAILABLE:
            raise ImportError("sentence-transformers required for CrossEncoderReranker")
        
        self.model_name = model_name
        self.device = device
        
        try:
            self.model = CrossEncoder(model_name, device=device)
            logger.info(f"CrossEncoderReranker initialized with {model_name} on {device}")
        except Exception as e:
            logger.error(f"Failed to load cross-encoder model: {e}")
            raise
    
    def rerank(self, items: List[Retrieved]) -> List[Retrieved]:
        """
        Rerank items using cross-encoder
        
        Args:
            items: List of retrieved chunks
            
        Returns:
            Reranked list of chunks
        """
        if not items:
            return items
        
        # Extract query from metadata
        query = items[0].chunk.meta.get('query', '') if items else ''
        
        if not query:
            # No query available, return sorted by existing score
            return sorted(items, key=lambda x: x.score or 0, reverse=True)
        
        logger.info(f"Cross-encoder reranking {len(items)} chunks")
        
        try:
            # Prepare pairs for cross-encoder
            pairs = [[query, item.chunk.text] for item in items]
            
            # Get scores from cross-encoder
            scores = self.model.predict(pairs)
            
            # Create new Retrieved objects with updated scores
            reranked_items = []
            for item, score in zip(items, scores):
                # Cross-encoder scores are already normalized
                reranked_items.append(replace(item, score=float(score)))
            
            # Sort by score
            reranked_items.sort(key=lambda x: x.score or 0, reverse=True)
            
            logger.info(f"Cross-encoder reranking complete. Top score: {reranked_items[0].score:.3f}")
            
            return reranked_items
            
        except Exception as e:
            logger.error(f"Cross-encoder reranking failed: {e}")
            logger.warning("Falling back to SimpleScoreReranker")
            return SimpleScoreReranker().rerank(items)


class SimpleScoreReranker(Reranker):
    """
    Simple heuristic-based reranker
    """
    
    def __init__(self, boost_recent: bool = True, boost_title_match: bool = True):
        """
        Initialize simple reranker
        
        Args:
            boost_recent: Whether to boost recent documents
            boost_title_match: Whether to boost title matches
        """
        self.boost_recent = boost_recent
        self.boost_title_match = boost_title_match
        logger.info("SimpleScoreReranker initialized")
    
    def rerank(self, items: List[Retrieved]) -> List[Retrieved]:
        """
        Rerank items using simple heuristics
        
        Args:
            items: List of retrieved chunks
            
        Returns:
            Reranked list of chunks
        """
        if not items:
            return items
        
        logger.info(f"Simple reranking {len(items)} chunks")
        
        # Extract query for title matching
        query = items[0].chunk.meta.get('query', '').lower() if items else ''
        
        reranked_items = []
        for item in items:
            # Start with existing score
            score = item.score or 0.5
            
            # Boost recent documents
            if self.boost_recent:
                created_at = item.chunk.meta.get('created_at')
                if created_at:
                    try:
                        # Parse timestamp
                        if isinstance(created_at, str):
                            doc_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        else:
                            doc_time = created_at
                        
                        # Calculate recency boost
                        age_days = (datetime.now() - doc_time).days
                        if age_days < 7:
                            score *= 1.2  # 20% boost for last week
                        elif age_days < 30:
                            score *= 1.1  # 10% boost for last month
                    except:
                        pass
            
            # Boost title matches
            if self.boost_title_match and query:
                title = item.chunk.meta.get('title', '').lower()
                if title and query in title:
                    score *= 1.3  # 30% boost for title match
            
            # Create new Retrieved object with updated score
            reranked_items.append(replace(item, score=min(score, 1.0)))  # Cap at 1.0
        
        # Sort by score
        reranked_items.sort(key=lambda x: x.score or 0, reverse=True)
        
        logger.info(f"Simple reranking complete. Top score: {reranked_items[0].score:.3f}")
        
        return reranked_items
