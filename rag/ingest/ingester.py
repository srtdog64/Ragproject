# ingest/ingester.py
from __future__ import annotations
import asyncio
from typing import List
from core.result import Result
from core.types import Document, Chunk
from core.interfaces import Chunker, Embedder, VectorStore

class Ingester:
    def __init__(self, chunker: Chunker, embedder: Embedder, store: VectorStore, maxParallel: int = 8):
        self._chunker = chunker
        self._embedder = embedder
        self._store = store
        self._maxParallel = max(1, maxParallel)

    async def ingest(self, docs: List[Document]) -> Result[int]:
        if len(docs) == 0:
            return Result.err("No documents to ingest.")
        chunks: List[Chunk] = []
        for d in docs:
            chunks.extend(self._chunker.chunk(d))
        await self._embedAndUpsert(chunks)
        return Result.ok(len(chunks))

    async def _embedAndUpsert(self, chunks: List[Chunk]) -> None:
        sem = asyncio.Semaphore(self._maxParallel)
        async def addBatch(batch: List[Chunk]) -> None:
            async with sem:
                vecs = self._embedder.embedTexts([c.text for c in batch])
                self._store.addMany(batch, vecs)
        # Batch in groups of 16
        tasks = []
        for i in range(0, len(chunks), 16):
            tasks.append(addBatch(chunks[i:i+16]))
        await asyncio.gather(*tasks)
