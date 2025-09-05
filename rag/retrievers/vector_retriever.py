# retrievers/vector_retriever.py
from __future__ import annotations
from typing import List, Optional, Dict, Any
from core.types import Retrieved
from core.interfaces import Retriever, VectorStore, Embedder

class VectorRetrieverImpl:
    def __init__(self, store: VectorStore, embedder: Embedder, metaFilter: Optional[Dict[str, Any]] = None):
        self._store = store
        self._embedder = embedder
        self._metaFilter = metaFilter

    def setMetaFilter(self, f: Optional[Dict[str, Any]]) -> None:
        self._metaFilter = f

    async def retrieve(self, query: str, k: int) -> List[Retrieved]:
        qVec = self._embedder.embedTexts([query])[0]
        return self._store.search(qVec, k, self._metaFilter)
