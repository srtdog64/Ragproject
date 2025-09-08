# core/policy.py
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Policy:
    maxContextChars: int = 12000
    defaulttopK: int = 5

    def getMaxContextChars(self) -> int:
        return self.maxContextChars

    def setMaxContextChars(self, n: int) -> None:
        self.maxContextChars = max(2000, n)

    def getDefaulttopK(self) -> int:
        return self.defaulttopK

    def setDefaulttopK(self, k: int) -> None:
        self.defaulttopK = max(1, k)
