# core/policy.py
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Policy:
    maxContextChars: int = 12000
    defaultTopK: int = 5

    def getMaxContextChars(self) -> int:
        return self.maxContextChars

    def setMaxContextChars(self, n: int) -> None:
        self.maxContextChars = max(2000, n)

    def getDefaultTopK(self) -> int:
        return self.defaultTopK

    def setDefaultTopK(self, k: int) -> None:
        self.defaultTopK = max(1, k)
