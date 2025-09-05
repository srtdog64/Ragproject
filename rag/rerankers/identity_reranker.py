# rerankers/identity_reranker.py
from __future__ import annotations
from typing import List
from core.types import Retrieved

class IdentityReranker:
    def rerank(self, items: List[Retrieved]) -> List[Retrieved]:
        return items
