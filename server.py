# server.py
from __future__ import annotations
import uuid, time, asyncio
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from di.container import Container
from core.policy import Policy
from core.result import Result
from core.types import Document, RagContext
from adapters.llm_client import GeminiLlm  # Changed to Gemini
from adapters.hash_embedder import HashEmbedder
from stores.memory_store import InMemoryVectorStore
from chunkers.overlap_chunker import SimpleOverlapChunker
from retrievers.vector_retriever import VectorRetrieverImpl
from rerankers.identity_reranker import IdentityReranker
from parsers.parser_builder import ParserBuilder
from ingest.ingester import Ingester
from pipeline.steps import (
    QueryExpansionStep, RetrieveStep, RerankStep,
    ContextCompressionStep, BuildPromptStep, GenerateStep, ParseStep
)
from pipeline.builder import PipelineBuilder

# ---------- Pydantic I/O ----------
class DocumentIn(BaseModel):
    id: str
    title: str
    source: str
    text: str

class IngestIn(BaseModel):
    documents: List[DocumentIn] = Field(min_items=1)

class AskIn(BaseModel):
    question: str = Field(min_length=1, max_length=10000)
    k: Optional[int] = Field(default=None, ge=1, le=20)

class AskOut(BaseModel):
    answer: str
    ctxIds: List[str]
    requestId: str
    latencyMs: int

# ---------- DI Container ----------
def buildContainer() -> Container:
    c = Container()
    c.register("policy", lambda _: Policy(maxContextChars=8000, defaultTopK=5))
    c.register("embedder", lambda _: HashEmbedder(dim=96))
    c.register("store", lambda _: InMemoryVectorStore())
    c.register("chunker", lambda _: SimpleOverlapChunker(size=800, overlap=120))
    c.register("llm", lambda _: GeminiLlm())  # Use Gemini with API key from .env
    c.register("reranker", lambda _: IdentityReranker())
    return c

# ---------- Assembly ----------
def buildPipeline(c: Container) -> tuple[Ingester, PipelineBuilder]:
    policy = c.resolve("policy")
    embedder = c.resolve("embedder")
    store = c.resolve("store")
    llm = c.resolve("llm")
    retriever = VectorRetrieverImpl(store=store, embedder=embedder)
    parser = ParserBuilder().setFormat("markdown-qa").build()  # Changed to markdown format for better readability

    ingester = Ingester(chunker=c.resolve("chunker"), embedder=embedder, store=store, maxParallel=8)
    pipeline = (
        PipelineBuilder()
        .add(QueryExpansionStep(expansions=0))
        .add(RetrieveStep(retriever=retriever, policy=policy))
        .add(RerankStep(reranker=c.resolve("reranker"), topK=policy.getDefaultTopK()))
        .add(ContextCompressionStep(policy=policy))
        .add(BuildPromptStep(systemHint="You are a helpful RAG assistant. Answer based on the context provided."))
        .add(GenerateStep(llm=llm, system="Be precise and helpful."))
        .add(ParseStep(parser=parser))
    )
    return ingester, pipeline

# ---------- App ----------
app = FastAPI(title="RAG Service with Gemini")

# CORS for local Qt6 development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "http://127.0.0.1:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_container = buildContainer()
_ingester, _pipelineBuilder = buildPipeline(_container)

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "RAG", "llm": "Gemini"}

@app.post("/ingest")
async def ingest(payload: IngestIn) -> dict:
    docs = [Document(**d.dict()) for d in payload.documents]
    res = await _ingester.ingest(docs)
    if res.isErr():
        raise HTTPException(status_code=400, detail=str(res.getError()))
    return {"ingestedChunks": res.getValue(), "documentCount": len(docs)}

@app.post("/ask", response_model=AskOut)
async def ask(body: AskIn) -> AskOut:
    rid = str(uuid.uuid4())
    t0 = time.time()
    policy = _container.resolve("policy")
    k = body.k if body.k is not None else policy.getDefaultTopK()

    ctx = RagContext(
        question=body.question, k=k,
        expandedQueries=[], retrieved=[], reranked=[],
        compressedCtx="", prompt="", rawLlm="", parsed=None  # type: ignore
    )
    pipeline = _pipelineBuilder.build()
    res = await pipeline.run(ctx)
    if res.isErr():
        raise HTTPException(status_code=500, detail=str(res.getError()))
    ans = res.getValue()
    dt = int((time.time() - t0) * 1000)
    return AskOut(answer=ans.text, ctxIds=ans.metadata.get("ctxIds", []), requestId=rid, latencyMs=dt)
