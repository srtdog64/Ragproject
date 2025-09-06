# stores/memory_store.py
from __future__ import annotations
from typing import List, Tuple, Dict, Any, Optional
from math import sqrt
import logging
from core.types import Chunk, Retrieved

logger = logging.getLogger(__name__)

class InMemoryVectorStore:
    def __init__(self):
        self._rows: List[Tuple[Chunk, List[float]]] = []
        logger.info("InMemoryVectorStore initialized")

    def addMany(self, chunks: List[Chunk], vectors: List[List[float]]) -> None:
        initial_count = len(self._rows)
        for i in range(len(chunks)):
            self._rows.append((chunks[i], vectors[i]))
        logger.info(f"Added {len(chunks)} chunks to store (total now: {len(self._rows)})")
        for chunk in chunks[:3]:  # Log first 3 chunks
            logger.debug(f"  Chunk {chunk.id}: {chunk.text[:50]}...")

    def upsert(self, chunk: Chunk, vector: List[float]) -> None:
        for i in range(len(self._rows)):
            if self._rows[i][0].id == chunk.id:
                self._rows[i] = (chunk, vector)
                return
        self._rows.append((chunk, vector))

    def deleteByDoc(self, docId: str) -> None:
        self._rows = [(c, v) for (c, v) in self._rows if c.docId != docId]

    def search(self, queryVector: List[float], k: int, metaFilter: Optional[Dict[str, Any]] = None) -> List[Retrieved]:
        logger.info(f"Searching with k={k}, vector dim={len(queryVector)}, total rows={len(self._rows)}")
        
        if not self._rows:
            logger.warning("Vector store is empty! No documents indexed.")
            return []
        
        scored = []
        for (c, v) in self._rows:
            if metaFilter is not None:
                ok = True
                for key, val in metaFilter.items():
                    if key not in c.meta or c.meta[key] != val:
                        ok = False
                        break
                if not ok:
                    continue
            s = self._cosSim(v, queryVector)
            scored.append((c, s))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:k]
        
        logger.info(f"Found {len(top)} results (scores: {[s for _, s in top[:3]]})")
        for r in top[:2]:  # Log top 2 results
            logger.debug(f"  Result: score={r[1]:.3f}, text={r[0].text[:50]}...")
        
        return [Retrieved(chunk=c, score=s) for (c, s) in top]

    def _cosSim(self, a: List[float], b: List[float]) -> float:
        if len(a) != len(b):
            logger.error(f"Vector dimension mismatch: {len(a)} != {len(b)}")
            return 0.0
        dot = 0.0
        na = 0.0
        nb = 0.0
        for i in range(len(a)):
            dot += a[i] * b[i]
            na += a[i] * a[i]
            nb += b[i] * b[i]
        denom = (sqrt(na) * sqrt(nb)) if (na > 0.0 and nb > 0.0) else 1e-9
        return dot / denom
