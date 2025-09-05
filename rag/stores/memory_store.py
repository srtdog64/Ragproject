# stores/memory_store.py
from __future__ import annotations
from typing import List, Tuple, Dict, Any, Optional
from math import sqrt
from core.types import Chunk, Retrieved

class InMemoryVectorStore:
    def __init__(self):
        self._rows: List[Tuple[Chunk, List[float]]] = []

    def addMany(self, chunks: List[Chunk], vectors: List[List[float]]) -> None:
        for i in range(len(chunks)):
            self._rows.append((chunks[i], vectors[i]))

    def upsert(self, chunk: Chunk, vector: List[float]) -> None:
        for i in range(len(self._rows)):
            if self._rows[i][0].id == chunk.id:
                self._rows[i] = (chunk, vector)
                return
        self._rows.append((chunk, vector))

    def deleteByDoc(self, docId: str) -> None:
        self._rows = [(c, v) for (c, v) in self._rows if c.docId != docId]

    def search(self, queryVector: List[float], k: int, metaFilter: Optional[Dict[str, Any]] = None) -> List[Retrieved]:
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
        return [Retrieved(chunk=c, score=s) for (c, s) in top]

    def _cosSim(self, a: List[float], b: List[float]) -> float:
        if len(a) != len(b):
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
