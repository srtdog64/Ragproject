# rerankers/hybrid_reranker.py
"""
Hybrid reranker combining multiple reranking strategies
"""
import logging
from typing import List, Dict
from core.interfaces import Reranker
from core.types import Retrieved
from dataclasses import replace
from .cross_encoder_reranker import SimpleScoreReranker
from .bm25_reranker import BM25Reranker

logger = logging.getLogger(__name__)


class HybridReranker(Reranker):
    """
    Hybrid reranker that combines multiple reranking methods
    """
    
    def __init__(self, weights: Dict[str, float] = None):
        """
        Initialize hybrid reranker
        
        Args:
            weights: Weight for each reranker type
        """
        self.weights = weights or {
            'semantic': 0.5,
            'bm25': 0.3,
            'simple': 0.2
        }
        
        # Normalize weights
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v/total for k, v in self.weights.items()}
        
        # Initialize sub-rerankers
        self.simple_reranker = SimpleScoreReranker()
        self.bm25_reranker = BM25Reranker()
        
        logger.info(f"HybridReranker initialized with weights: {self.weights}")
    
    def rerank(self, items: List[Retrieved]) -> List[Retrieved]:
        """
        Rerank using multiple methods and combine scores
        
        Args:
            items: List of retrieved chunks
            
        Returns:
            Reranked list of chunks
        """
        if not items:
            return items
        
        logger.info(f"Hybrid reranking {len(items)} chunks")
        
        # Store original scores (semantic)
        original_scores = {id(item): item.score or 0 for item in items}
        
        # Get BM25 scores
        bm25_items = self.bm25_reranker.rerank(items)
        bm25_scores = {id(orig): new.score or 0 
                      for orig, new in zip(items, bm25_items)}
        
        # Get simple reranker scores  
        simple_items = self.simple_reranker.rerank(items)
        simple_scores = {id(orig): new.score or 0 
                        for orig, new in zip(items, simple_items)}
        
        # Combine scores with weights
        reranked_items = []
        for item in items:
            item_id = id(item)
            
            # Get individual scores
            semantic_score = original_scores[item_id]
            bm25_score = bm25_scores[item_id]
            simple_score = simple_scores[item_id]
            
            # Weighted combination
            combined_score = (
                self.weights.get('semantic', 0.5) * semantic_score +
                self.weights.get('bm25', 0.3) * bm25_score +
                self.weights.get('simple', 0.2) * simple_score
            )
            
            # Create new Retrieved object with combined score
            reranked_items.append(replace(item, score=combined_score))
        
        # Sort by combined score
        reranked_items.sort(key=lambda x: x.score or 0, reverse=True)
        
        logger.info(f"Hybrid reranking complete. Top score: {reranked_items[0].score:.3f}")
        return reranked_items
