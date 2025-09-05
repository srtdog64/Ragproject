# server.py
from __future__ import annotations
import uuid, time, asyncio
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config_loader import config
from di.container import Container
from core.policy import Policy
from core.result import Result
from core.types import Document, RagContext
from adapters.llm_client import LlmFactory  # Use factory for dynamic LLM selection
from adapters.hash_embedder import HashEmbedder
from stores.memory_store import InMemoryVectorStore
from chunkers.registry import registry
from chunkers.wrapper import ChunkerWrapper
from chunkers.api_router import router as chunkers_router
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
    provider: Optional[str] = Field(default=None)  # Changed from model_provider
    model: Optional[str] = Field(default=None)  # Changed from model_name
    
    class Config:
        protected_namespaces = ()  # Disable protected namespace check

class AskOut(BaseModel):
    answer: str
    ctxIds: List[str]
    requestId: str
    latencyMs: int

# ---------- DI Container ----------
def buildContainer() -> Container:
    c = Container()
    
    # Load configuration
    policy_config = config.get_section('policy')
    embedder_config = config.get_section('embedder')
    ingester_config = config.get_section('ingester')
    chunker_config = config.get_section('chunker')
    
    # Register components with config values
    c.register("policy", lambda _: Policy(
        maxContextChars=policy_config.get('maxContextChars', 8000),
        defaultTopK=policy_config.get('defaultTopK', 5)
    ))
    
    c.register("embedder", lambda _: HashEmbedder(
        dim=embedder_config.get('dimension', 96)
    ))
    
    c.register("store", lambda _: InMemoryVectorStore())
    
    # Initialize chunker registry with config
    if chunker_config:
        if 'default_strategy' in chunker_config:
            registry.set_strategy(chunker_config['default_strategy'])
        if 'default_params' in chunker_config:
            registry.set_params(**chunker_config['default_params'])
    
    c.register("chunker", lambda _: ChunkerWrapper())
    c.register("llm", lambda _: LlmFactory.create())  # Use factory to create LLM based on config
    c.register("reranker", lambda _: IdentityReranker())
    
    return c

# ---------- Assembly ----------
def buildPipeline(c: Container) -> tuple[Ingester, PipelineBuilder]:
    policy = c.resolve("policy")
    embedder = c.resolve("embedder")
    store = c.resolve("store")
    llm = c.resolve("llm")
    retriever = VectorRetrieverImpl(store=store, embedder=embedder)
    
    # Load pipeline config
    pipeline_config = config.get_section('pipeline')
    ingester_config = config.get_section('ingester')
    
    # Create parser with config
    parser_format = pipeline_config.get('parsing', {}).get('format', 'markdown-qa')
    parser = ParserBuilder().setFormat(parser_format).build()

    # Create ingester with config
    ingester = Ingester(
        chunker=c.resolve("chunker"),
        embedder=embedder,
        store=store,
        maxParallel=ingester_config.get('max_parallel', 8)
    )
    
    # Build pipeline with config
    pipeline_builder = PipelineBuilder()
    
    # Query expansion
    if pipeline_config.get('query_expansion', {}).get('enabled', False):
        expansions = pipeline_config['query_expansion'].get('expansions', 0)
        pipeline_builder.add(QueryExpansionStep(expansions=expansions))
    
    # Retrieval
    if pipeline_config.get('retrieval', {}).get('enabled', True):
        pipeline_builder.add(RetrieveStep(retriever=retriever, policy=policy))
    
    # Reranking
    if pipeline_config.get('reranking', {}).get('enabled', True):
        topK = pipeline_config['reranking'].get('topK') or policy.getDefaultTopK()
        pipeline_builder.add(RerankStep(reranker=c.resolve("reranker"), topK=topK))
    
    # Context compression
    if pipeline_config.get('context_compression', {}).get('enabled', True):
        pipeline_builder.add(ContextCompressionStep(policy=policy))
    
    # Prompt building
    prompt_config = pipeline_config.get('prompt', {})
    system_hint = prompt_config.get('system_hint', 'You are a helpful RAG assistant.')
    system_msg = prompt_config.get('system_message', 'Be precise and helpful.')
    pipeline_builder.add(BuildPromptStep(systemHint=system_hint))
    
    # Generation
    if pipeline_config.get('generation', {}).get('enabled', True):
        pipeline_builder.add(GenerateStep(llm=llm, system=system_msg))
    
    # Parsing
    if pipeline_config.get('parsing', {}).get('enabled', True):
        pipeline_builder.add(ParseStep(parser=parser))
    
    return ingester, pipeline_builder

# ---------- App ----------
app = FastAPI(title="RAG Service with Gemini")

# Include the chunkers router
app.include_router(chunkers_router)

# CORS configuration from config file
cors_config = config.get_section('cors')
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config.get('allow_origins', ["*"]),
    allow_credentials=cors_config.get('allow_credentials', True),
    allow_methods=cors_config.get('allow_methods', ["*"]),
    allow_headers=cors_config.get('allow_headers', ["*"]),
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

@app.get("/config/reload")
async def reload_config():
    """Reload configuration from file"""
    try:
        config.reload()
        return {"message": "Configuration reloaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
