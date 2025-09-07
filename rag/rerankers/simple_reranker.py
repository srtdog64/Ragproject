# rerankers/simple_reranker.py
"""
Simple reranker that doesn't require query parameter
"""
import logging
from typing import List
from core.interfaces import Reranker
from core.types import Retrieved

logger = logging.getLogger(__name__)


class SimpleReranker(Reranker):
    """
    Simple reranker using only the existing scores
    """
    
    def rerank(self, items: List[Retrieved]) -> List[Retrieved]:
        """
        Rerank items by their existing scores
        
        Args:
            items: List of retrieved items
            
        Returns:
            Reranked list
        """
        if not items:
            return items
        
        # Simply sort by existing scores
        items.sort(key=lambda x: x.score or 0, reverse=True)
        
        return items
