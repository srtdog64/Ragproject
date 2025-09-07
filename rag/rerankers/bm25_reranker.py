# rerankers/bm25_reranker.py
"""
BM25-based reranker for Korean and multilingual documents
"""
import logging
from typing import List
from core.interfaces import Reranker
from core.types import Retrieved
from dataclasses import replace

logger = logging.getLogger(__name__)

# BM25 implementation without external dependency
class BM25:
    """Simple BM25 implementation"""
    
    def __init__(self, corpus, k1=1.2, b=0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.avgdl = sum(len(doc) for doc in corpus) / len(corpus) if corpus else 0
        self.corpus = corpus
        self.doc_freqs = {}
        self.idf = {}
        
        # Calculate document frequencies
        for doc in corpus:
            doc_set = set(doc)
            for word in doc_set:
                self.doc_freqs[word] = self.doc_freqs.get(word, 0) + 1
        
        # Calculate IDF scores
        for word, freq in self.doc_freqs.items():
            self.idf[word] = self._calc_idf(freq)
    
    def _calc_idf(self, doc_freq):
        """Calculate IDF score"""
        import math
        return math.log((self.corpus_size - doc_freq + 0.5) / (doc_freq + 0.5) + 1)
    
    def get_scores(self, query):
        """Get BM25 scores for all documents"""
        scores = []
        for doc in self.corpus:
            scores.append(self._score(query, doc))
        return scores
    
    def _score(self, query, doc):
        """Calculate BM25 score for a single document"""
        score = 0.0
        doc_len = len(doc)
        
        for word in query:
            if word not in self.doc_freqs:
                continue
            
            freq = doc.count(word)
            score += (self.idf[word] * freq * (self.k1 + 1) /
                     (freq + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)))
        
        return score


class BM25Reranker(Reranker):
    """
    BM25-based reranker for traditional keyword matching
    Good for Korean and exact term matching
    """
    
    def __init__(self, k1: float = 1.2, b: float = 0.75):
        """
        Initialize BM25 reranker
        
        Args:
            k1: Term frequency saturation parameter
            b: Length normalization parameter
        """
        self.k1 = k1
        self.b = b
        logger.info(f"BM25Reranker initialized with k1={k1}, b={b}")
    
    def rerank(self, items: List[Retrieved]) -> List[Retrieved]:
        """
        Rerank items using BM25 scoring
        
        Args:
            items: List of retrieved chunks
            
        Returns:
            Reranked list of chunks
        """
        if not items:
            return items
        
        # Extract query from first item's metadata if available
        query = items[0].chunk.meta.get('query', '') if items else ''
        
        logger.info(f"BM25 reranking {len(items)} chunks")
        
        try:
            # Tokenize documents (simple space-based for now)
            # For better Korean support, use a proper tokenizer
            corpus = [item.chunk.text.lower().split() for item in items]
            query_tokens = query.lower().split() if query else []
            
            if not query_tokens:
                # If no query, just return items sorted by existing score
                return sorted(items, key=lambda x: x.score or 0, reverse=True)
            
            # Create BM25 instance
            bm25 = BM25(corpus, k1=self.k1, b=self.b)
            
            # Get BM25 scores
            scores = bm25.get_scores(query_tokens)
            
            # Create new Retrieved objects with updated scores
            reranked_items = []
            for i, (item, bm25_score) in enumerate(zip(items, scores)):
                # Normalize BM25 score to 0-1 range
                max_score = max(scores) if scores else 1
                if max_score > 0:
                    normalized_score = bm25_score / max_score
                else:
                    normalized_score = 0
                
                # Combine with existing score (if any)
                if item.score is not None:
                    # Weight: 60% embedding, 40% BM25
                    new_score = 0.6 * item.score + 0.4 * normalized_score
                else:
                    new_score = normalized_score
                
                # Create new Retrieved object with updated score
                reranked_items.append(replace(item, score=new_score))
            
            # Sort by combined score
            reranked_items.sort(key=lambda x: x.score or 0, reverse=True)
            
            logger.info(f"BM25 reranking complete. Top score: {reranked_items[0].score:.3f}")
            
            return reranked_items
            
        except Exception as e:
            logger.error(f"BM25 reranking failed: {e}")
            logger.warning("Returning original order")
            return items
