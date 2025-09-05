# adapters/hash_embedder.py
from __future__ import annotations
import hashlib
from typing import List

class HashEmbedder:
    def __init__(self, dim: int = 96):
        self._dim = max(32, dim)

    def getDim(self) -> int:
        return self._dim

    def setDim(self, d: int) -> None:
        self._dim = max(32, d)

    def embedTexts(self, texts: List[str]) -> List[List[float]]:
        return [self._hashToVec(t) for t in texts]

    def _hashToVec(self, text: str) -> List[float]:
        h = hashlib.sha256(text.encode("utf-8")).digest()
        nums = [b for b in h]
        return [float(nums[i % len(nums)]) / 255.0 for i in range(self._dim)]
