# rerankers/cross_encoder_reranker.py
"""
Cross-Encoder based reranker for improving retrieval quality
"""
from __future__ import annotations
from typing import List, Tuple
import logging
from sentence_transformers import CrossEncoder
from core.types import Retrieved
from core.interfaces import Reranker

logger = logging.getLogger(__name__)

class CrossEncoderReranker(Reranker):
    """
    Reranker using Cross-Encoder models for more accurate relevance scoring
    """
    
    def __init__(self, 
                 model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
                 device: str = "cpu",
                 max_length: int = 512):
        """
        Initialize Cross-Encoder reranker
        
        Args:
            model_name: Name of the cross-encoder model to use
            device: Device to run the model on ('cpu' or 'cuda')
            max_length: Maximum sequence length for the model
        """
        self.model_name = model_name
        self.device = device
        self.max_length = max_length
        
        # Load the cross-encoder model
        try:
            self.model = CrossEncoder(model_name, device=device, max_length=max_length)
            logger.info(f"CrossEncoderReranker: Loaded model '{model_name}' on {device}")
        except Exception as e:
            logger.error(f"Failed to load cross-encoder model: {e}")
            raise
    
    def rerank(self, retrieved: List[Retrieved], query: str = None) -> List[Retrieved]:
        """
        Rerank retrieved documents based on their relevance to the query
        
        Args:
            retrieved: List of retrieved documents with initial scores
            query: The original query (required for cross-encoder)
        
        Returns:
            Reranked list of Retrieved objects
        """
        if not retrieved:
            return retrieved
        
        if not query:
            logger.warning("CrossEncoderReranker: No query provided, returning original order")
            return retrieved
        
        logger.info(f"CrossEncoderReranker: Reranking {len(retrieved)} documents")
        
        # Prepare pairs of (query, document) for the cross-encoder
        pairs = [(query, r.chunk.text) for r in retrieved]
        
        # Get relevance scores from the cross-encoder
        try:
            scores = self.model.predict(pairs)
            logger.debug(f"CrossEncoderReranker: Computed scores: {scores[:5]}")  # Log first 5 scores
        except Exception as e:
            logger.error(f"CrossEncoderReranker: Failed to compute scores: {e}")
            return retrieved  # Return original order on failure
        
        # Create new Retrieved objects with updated scores
        reranked = []
        for i, r in enumerate(retrieved):
            # Use cross-encoder score as the new score
            new_retrieved = Retrieved(
                chunk=r.chunk,
                score=float(scores[i])  # Cross-encoder score
            )
            reranked.append(new_retrieved)
        
        # Sort by new scores (descending)
        reranked.sort(key=lambda x: x.score, reverse=True)
        
        logger.info(f"CrossEncoderReranker: Top scores after reranking: {[r.score for r in reranked[:3]]}")
        
        return reranked


class SimpleScoreReranker(Reranker):
    """
    Simple reranker that combines original retrieval score with other factors
    """
    
    def __init__(self, boost_recent: bool = True, boost_title_match: bool = True):
        """
        Initialize simple score-based reranker
        
        Args:
            boost_recent: Whether to boost more recent documents
            boost_title_match: Whether to boost documents with query terms in title
        """
        self.boost_recent = boost_recent
        self.boost_title_match = boost_title_match
        logger.info("SimpleScoreReranker initialized")
    
    def rerank(self, retrieved: List[Retrieved], query: str = None) -> List[Retrieved]:
        """
        Rerank based on simple heuristics
        """
        if not retrieved:
            return retrieved
        
        logger.info(f"SimpleScoreReranker: Reranking {len(retrieved)} documents")
        
        reranked = []
        query_lower = query.lower() if query else ""
        
        for r in retrieved:
            # Start with original score
            new_score = r.score
            
            # Boost if query terms appear in title
            if self.boost_title_match and query:
                # Get title from meta or use empty string if not available
                title = r.chunk.meta.get('docTitle', '').lower() if r.chunk.meta else ''
                if not title:
                    title = r.chunk.meta.get('title', '').lower() if r.chunk.meta else ''
                
                # Check for query terms in title
                query_terms = query_lower.split()
                matches = sum(1 for term in query_terms if term in title)
                if matches > 0:
                    # Boost by 20% for each matching term
                    new_score *= (1 + 0.2 * matches)
                    logger.debug(f"Boosted score for title match: {title}")
            
            # Boost based on chunk position (earlier chunks often more relevant)
            chunk_index = r.chunk.meta.get('chunkIndex', 0) if r.chunk.meta else 0
            if chunk_index == 0:
                new_score *= 1.1  # 10% boost for first chunk
            
            # Create new Retrieved with adjusted score
            reranked.append(Retrieved(
                chunk=r.chunk,
                score=new_score
            ))
        
        # Sort by new scores
        reranked.sort(key=lambda x: x.score, reverse=True)
        
        logger.info(f"SimpleScoreReranker: Top scores after reranking: {[r.score for r in reranked[:3]]}")
        
        return reranked
