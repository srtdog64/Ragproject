# adapters/embedders/base.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Sequence, Generic, TypeVar, Dict
import threading
import math
import hashlib

T = TypeVar("T")

@dataclass(frozen=True)
class Result(Generic[T]):
    ok: bool
    value: Optional[T] = None
    error: Optional[str] = None
    
    @staticmethod
    def Ok(v: T) -> "Result[T]": 
        return Result(True, v, None)
    
    @staticmethod
    def Err(msg: str) -> "Result[T]": 
        return Result(False, None, msg)

class IEmbedder:
    def getDim(self) -> int: 
        raise NotImplementedError
    
    def getName(self) -> str: 
        raise NotImplementedError
    
    def embedText(self, text: str) -> List[float]: 
        raise NotImplementedError
    
    def embedTexts(self, texts: Sequence[str]) -> List[List[float]]: 
        raise NotImplementedError

def l2norm(vec: List[float]) -> List[float]:
    s = math.sqrt(sum(x*x for x in vec)) + 1e-12
    return [x / s for x in vec]

def koRatio(texts: Sequence[str]) -> float:
    total = sum(len(t) for t in texts)
    if total <= 0:
        return 0.0
    kor = sum(1 for t in texts for ch in t if "\uac00" <= ch <= "\ud7af")
    return float(kor) / float(total)

class FallbackEmbedder(IEmbedder):
    def __init__(self, dim: int = 384, normalize: bool = True, name: str = "fallback"):
        self._dim = int(dim)
        self._normalize = bool(normalize)
        self._name = name

    def getDim(self) -> int: 
        return self._dim
    
    def getName(self) -> str: 
        return self._name

    def embedText(self, text: str) -> List[float]:
        return self.embedTexts([text])[0]

    def embedTexts(self, texts: Sequence[str]) -> List[List[float]]:
        out: List[List[float]] = []
        for t in texts:
            tl = (t or "").lower()
            feats: List[float] = []
            
            # Character frequency features
            for c in "abcdefghijklmnopqrstuvwxyz":
                feats.append(tl.count(c) / max(1, len(tl)))
            
            # Word-level features
            words = tl.split()
            feats.append(len(words) / 100.0)
            avgw = (sum(len(w) for w in words) / max(1, len(words))) / 10.0
            feats.append(avgw)
            
            # Domain-specific hints
            hints = ["rag","retrieval","augmented","generation","ai","llm",
                     "document","context","question","answer","chunk","embed"]
            for h in hints:
                feats.append(1.0 if h in tl else 0.0)
            
            # Pad with deterministic hash values
            while len(feats) < self._dim:
                idx = len(feats)
                h = hashlib.md5(f"{tl}|{idx}".encode()).digest()
                feats.append(h[0] / 255.0)
            
            vec = feats[: self._dim]
            out.append(l2norm(vec) if self._normalize else vec)
        
        return out
