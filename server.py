# server.py
from __future__ import annotations
import uuid, time, asyncio
import logging
import traceback
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from config_loader import config
from di.container import Container
from core.policy import Policy
from core.result import Result
from core.types import Document, RagContext
from adapters.llm_client import LlmFactory  # Use factory for dynamic LLM selection
from adapters.embedders.manager import EmbedderManager  # New embedder manager
from adapters.semantic_embedder import EmbedderFactory  # Keep for backward compatibility
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
    
    # Create embedder manager from YAML config
    try:
        embedder_manager = EmbedderManager.fromYaml("config/embeddings.yml")
        c.register("embedder_manager", lambda _: embedder_manager)
        # Register default embedder for backward compatibility
        c.register("embedder", lambda _: embedder_manager.getDefaultEmbedder())
        print("✅ Embedder manager initialized successfully")
    except Exception as e:
        print(f"⚠️ Warning: Failed to load embedder manager: {e}")
        # Fallback to old factory method
        try:
            c.register("embedder", lambda _: EmbedderFactory.create(embedder_config))
            print("✅ Using legacy embedder factory")
        except RuntimeError as e2:
            print(f"❌ CRITICAL ERROR: {e2}")
            print("The system cannot function without a proper embedder.")
            raise
    
    # Create singleton store instance
    store_instance = InMemoryVectorStore()
    c.register("store", lambda _: store_instance)  # Always return the same instance
    
    # Initialize chunker registry with config BEFORE creating wrapper
    if chunker_config:
        try:
            if 'default_strategy' in chunker_config:
                registry.set_strategy(chunker_config['default_strategy'])
            if 'default_params' in chunker_config:
                registry.set_params(**chunker_config['default_params'])
        except Exception as e:
            logger.warning(f"Failed to apply chunker config: {e}")
            # Continue with defaults
    
    # Ensure registry is properly initialized
    try:
        current_strategy = registry.get_current_strategy()
        logger.info(f"Chunker registry initialized with strategy: {current_strategy}")
    except Exception as e:
        logger.error(f"Chunker registry initialization failed: {e}")
        # Try to recover
        registry.set_strategy("adaptive")
    
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
    
    # Query expansion - always add, but with 0 expansions if disabled
    if pipeline_config.get('query_expansion', {}).get('enabled', False):
        expansions = pipeline_config['query_expansion'].get('expansions', 0)
        pipeline_builder.add(QueryExpansionStep(expansions=expansions))
    else:
        # Even if disabled, we need to set the basic query
        pipeline_builder.add(QueryExpansionStep(expansions=0))
    
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
    
    try:
        policy = _container.resolve("policy")
        k = body.k if body.k is not None else policy.getDefaultTopK()

        ctx = RagContext(
            question=body.question, k=k,
            expandedQueries=[], retrieved=[], reranked=[],
            compressedCtx="", prompt="", rawLlm="", parsed=None  # type: ignore
        )
        
        # Build and run pipeline
        pipeline = _pipelineBuilder.build()
        res = await pipeline.run(ctx)
        
        if res.isErr():
            error_msg = str(res.getError())
            logger.error(f"Pipeline error for request {rid}: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Pipeline error: {error_msg}")
        
        ans = res.getValue()
        dt = int((time.time() - t0) * 1000)
        
        logger.info(f"Request {rid} completed in {dt}ms")
        return AskOut(
            answer=ans.text, 
            ctxIds=ans.metadata.get("ctxIds", []), 
            requestId=rid, 
            latencyMs=dt
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in /ask endpoint for request {rid}:")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/config/reload")
async def reload_config():
    """Reload configuration from file"""
    try:
        config.reload()
        return {"message": "Configuration reloaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
