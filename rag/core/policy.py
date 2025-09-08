# core/policy.py
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Policy:
    maxContextChars: int = 12000
    defaultcontext_chunk: int = 5

    def getMaxContextChars(self) -> int:
        return self.maxContextChars

    def setMaxContextChars(self, n: int) -> None:
        self.maxContextChars = max(2000, n)

    def getDefaultcontext_chunk(self) -> int:
        return self.defaultcontext_chunk

    def setDefaultcontext_chunk(self, k: int) -> None:
        self.defaultcontext_chunk = max(1, k)
