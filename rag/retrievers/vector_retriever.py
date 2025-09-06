# retrievers/vector_retriever.py
from __future__ import annotations
from typing import List, Optional, Dict, Any
import logging
from core.types import Retrieved
from core.interfaces import Retriever, VectorStore, Embedder

logger = logging.getLogger(__name__)

class VectorRetrieverImpl:
    def __init__(self, store: VectorStore, embedder: Embedder, metaFilter: Optional[Dict[str, Any]] = None):
        self._store = store
        self._embedder = embedder
        self._metaFilter = metaFilter
        logger.info(f"VectorRetriever initialized with store: {type(store).__name__}")

    def setMetaFilter(self, f: Optional[Dict[str, Any]]) -> None:
        self._metaFilter = f

    async def retrieve(self, query: str, k: int) -> List[Retrieved]:
        logger.info(f"Retrieving for query: '{query[:50]}...' with k={k}")
        qVec = self._embedder.embedTexts([query])[0]
        logger.debug(f"Query vector dimension: {len(qVec)}")
        
        results = self._store.search(qVec, k, self._metaFilter)
        logger.info(f"Retrieved {len(results)} results")
        
        if results:
            for i, r in enumerate(results[:2]):
                logger.debug(f"  Result {i}: score={r.score:.3f}, text={r.chunk.text[:50]}...")
        else:
            logger.warning("No results found!")
            
        return results
