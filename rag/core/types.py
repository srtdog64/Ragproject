# core/types.py
from __future__ import annotations
from dataclasses import dataclass, replace
from typing import List, Dict, Any

@dataclass(frozen=True)
class Document:
    id: str
    title: str
    source: str
    text: str

@dataclass(frozen=True)
class Chunk:
    id: str
    docId: str
    text: str
    meta: Dict[str, Any]

@dataclass(frozen=True)
class Retrieved:
    chunk: Chunk
    score: float

@dataclass(frozen=True)
class Answer:
    text: str
    metadata: Dict[str, Any]

@dataclass(frozen=True)
class RagContext:
    question: str
    k: int
    expandedQueries: List[str]
    retrieved: List[Retrieved]
    reranked: List[Retrieved]
    compressedCtx: str
    prompt: str
    rawLlm: str
    parsed: Answer

    def withExpanded(self, qs: List[str]) -> "RagContext":
        return replace(self, expandedQueries=list(qs))

    def withRetrieved(self, items: List[Retrieved]) -> "RagContext":
        return replace(self, retrieved=list(items))

    def withReranked(self, items: List[Retrieved]) -> "RagContext":
        return replace(self, reranked=list(items))

    def withCompressed(self, ctx: str) -> "RagContext":
        return replace(self, compressedCtx=ctx)

    def withPrompt(self, p: str) -> "RagContext":
        return replace(self, prompt=p)

    def withRawLlm(self, s: str) -> "RagContext":
        return replace(self, rawLlm=s)

    def withParsed(self, a: Answer) -> "RagContext":
        return replace(self, parsed=a)
