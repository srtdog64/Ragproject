# rerankers/cohere_reranker.py
"""
Cohere API-based reranker
"""
import logging
from typing import List
from core.interfaces import Reranker
from core.types import Retrieved
from dataclasses import replace
import os

logger = logging.getLogger(__name__)

try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False
    logger.warning("Cohere library not installed. Install with: pip install cohere")


class CohereReranker(Reranker):
    """
    Cohere API-based reranker
    High quality but requires API key
    """
    
    def __init__(self, api_key: str = None, model: str = "rerank-english-v2.0"):
        """
        Initialize Cohere reranker
        
        Args:
            api_key: Cohere API key (or set COHERE_API_KEY env var)
            model: Reranker model name
        """
        if not COHERE_AVAILABLE:
            raise ImportError("Cohere library not installed")
        
        api_key = api_key or os.getenv("COHERE_API_KEY")
        if not api_key:
            raise ValueError("Cohere API key required")
        
        self.client = cohere.Client(api_key)
        self.model = model
        logger.info(f"CohereReranker initialized with model: {model}")
    
    def rerank(self, items: List[Retrieved]) -> List[Retrieved]:
        """
        Rerank chunks using Cohere API
        
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
        
        logger.info(f"Cohere reranking {len(items)} chunks")
        
        try:
            # Prepare documents for Cohere
            documents = [item.chunk.text for item in items]
            
            # Call Cohere rerank API
            response = self.client.rerank(
                query=query,
                documents=documents,
                model=self.model,
                top_n=len(items)  # Return all items, just reordered
            )
            
            # Create reranked list
            reranked_items = []
            for result in response.results:
                idx = result.index
                original_item = items[idx]
                # Create new Retrieved object with Cohere score
                reranked_items.append(
                    replace(original_item, score=result.relevance_score)
                )
            
            logger.info(f"Cohere reranking complete. Top score: {reranked_items[0].score:.3f}")
            return reranked_items
            
        except Exception as e:
            logger.error(f"Cohere reranking failed: {e}")
            logger.warning("Returning original order")
            return sorted(items, key=lambda x: x.score or 0, reverse=True)
