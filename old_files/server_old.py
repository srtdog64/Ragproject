# server.py
from __future__ import annotations
import os
import sys
import uuid, time, asyncio
import logging
import traceback
import yaml
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from config_loader import config
from rag.di.container import Container
from rag.core.policy import Policy
from rag.core.result import Result
from rag.core.types import Document, RagContext
from rag.adapters.llm_client import LlmFactory  # Use factory for dynamic LLM selection
from rag.adapters.embedders.manager import EmbedderManager  # New embedder manager
from rag.adapters.semantic_embedder import EmbedderFactory  # Keep for backward compatibility
from rag.stores.memory_store import InMemoryVectorStore
from rag.chunkers.registry import registry
from rag.chunkers.wrapper import ChunkerWrapper
from rag.chunkers.api_router import router as chunkers_router
from rag.retrievers.vector_retriever import VectorRetrieverImpl
from rag.rerankers.factory import RerankerFactory
from rag.parsers.parser_builder import ParserBuilder
from rag.ingest.ingester import Ingester
from rag.pipeline.steps import (
    QueryExpansionStep, RetrieveStep, RerankStep,
    ContextCompressionStep, BuildPromptStep, GenerateStep, ParseStep
)
from rag.pipeline.builder import PipelineBuilder

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
    k: Optional[int] = Field(default=None, ge=1, le=100)
    provider: Optional[str] = Field(default=None)  # Changed from model_provider
    model: Optional[str] = Field(default=None)  # Changed from model_name
    strict_mode: Optional[bool] = Field(default=False)  # Add strict mode flag
    
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
    store_config = config.get_section('store')
    
    # Register components with config values
    c.register("policy", lambda _: Policy(
        maxContextChars=policy_config.get('maxContextChars', 8000),
        defaultcontext_chunk=policy_config.get('defaultcontext_chunk', 5)
    ))
    
    # Create embedder manager from YAML config
    embedder_manager = None
    default_embedder = None
    
    try:
        embedder_manager = EmbedderManager.fromYaml("config/embeddings.yml")
        c.register("embedder_manager", lambda _: embedder_manager)
        # Register default embedder for backward compatibility
        default_embedder = embedder_manager.getDefaultEmbedder()
        c.register("embedder", lambda _: default_embedder)
        logger.info("Embedder manager initialized successfully")
    except Exception as e:
        logger.warning(f"Warning: Failed to load embedder manager: {e}")
        # Fallback to old factory method
        try:
            default_embedder = EmbedderFactory.create(embedder_config)
            c.register("embedder", lambda _: default_embedder)
            logger.info("Using legacy embedder factory")
        except RuntimeError as e2:
            logger.error(f"CRITICAL ERROR: {e2}")
            logger.error("The system cannot function without a proper embedder.")
            raise
    
    # Create vector store based on config
    store_config = config.get_section('store')
    store_type = store_config.get('type', 'memory')
    
    # Get embedder info for namespace
    embedding_model = None
    embedding_dim = None
    
    # Try to get info from the actual embedder instance
    if default_embedder:
        # Check for model_name attribute
        if hasattr(default_embedder, 'model_name'):
            embedding_model = default_embedder.model_name
        elif hasattr(default_embedder, 'model'):
            embedding_model = str(default_embedder.model)
        
        # Check for dimension attribute
        if hasattr(default_embedder, 'dimension'):
            embedding_dim = default_embedder.dimension
        elif hasattr(default_embedder, 'embedding_dim'):
            embedding_dim = default_embedder.embedding_dim
    
    # Fallback to config values if not found
    if not embedding_model and embedder_config:
        default_embedder_key = embedder_config.get('default_embedder', 'semantic')
        if default_embedder_key == 'semantic':
            embedding_model = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            embedding_dim = 384
    
    if store_type == 'chroma':
        from rag.stores.chroma_store import ChromaVectorStore
        persist_dir = store_config.get('persist_directory', './chroma_db')
        
        # Handle relative and absolute paths
        if not os.path.isabs(persist_dir):
            # If relative, make it relative to project root
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            persist_dir = os.path.join(project_root, persist_dir)
        
        # Normalize path
        persist_dir = os.path.normpath(persist_dir)
        
        collection = store_config.get('collection_name', 'rag_documents')
        
        # Log the actual path being used
        logger.info(f"ChromaDB persist_directory: {persist_dir}")
        logger.info(f"Directory exists: {os.path.exists(persist_dir)}")
        
        # Ensure directory exists
        os.makedirs(persist_dir, exist_ok=True)
        
        store_instance = ChromaVectorStore(
            persist_directory=persist_dir,
            collection_name=collection,
            embedding_model=embedding_model,
            embedding_dim=embedding_dim
        )
        logger.info(f"Using ChromaDB vector store at: {persist_dir}")
        logger.info(f"  Collection: {collection}")
        if embedding_model:
            logger.info(f"  Namespace for model: {embedding_model}")
    elif store_type == 'faiss':
        # TODO: Implement FAISS store with namespace support
        logger.info("FAISS store not yet implemented, falling back to memory")
        store_instance = InMemoryVectorStore()
    else:
        # Default to in-memory store
        store_instance = InMemoryVectorStore()
        logger.warning("Using InMemoryVectorStore (non-persistent) - data will be lost on restart!")
    
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
    # Create reranker based on config
    reranker_config = config.get_section('reranker')
    reranker_type = reranker_config.get('type', 'identity')
    reranker = RerankerFactory.create(
        reranker_type=reranker_type,
        model=reranker_config.get('model'),
        device=reranker_config.get('device', 'cpu')
    )
    c.register("reranker", lambda _: reranker)
    
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
        context_chunk = pipeline_config['reranking'].get('context_chunk') or policy.getDefaultcontext_chunk()
        pipeline_builder.add(RerankStep(reranker=c.resolve("reranker"), context_chunk=context_chunk))
    
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

# Global variables for components
_container = None
_ingester = None
_pipelineBuilder = None

def rebuild_components() -> None:
    """Recreate DI container and pipeline after config change."""
    global _container, _ingester, _pipelineBuilder
    try:
        logger.info("[rebuild_components] Starting rebuild...")
        _container = buildContainer()
        logger.info("[rebuild_components] Container built successfully")
        _ingester, _pipelineBuilder = buildPipeline(_container)
        logger.info("[rebuild_components] Pipeline built successfully")
    except Exception as e:
        logger.error(f"[rebuild_components] Failed: {e}")
        logger.error(traceback.format_exc())
        raise

def initialize_components():
    """Initialize RAG components"""
    global _container, _ingester, _pipelineBuilder
    
    try:
        logger.info("="*60)
        logger.info("[INIT] Starting component initialization...")
        logger.info("="*60)
        
        _container = buildContainer()
        logger.info("[INIT] ✅ Container built successfully")
        logger.info(f"[INIT] Container type: {type(_container)}")
        
        _ingester, _pipelineBuilder = buildPipeline(_container)
        logger.info("[INIT] ✅ Pipeline built successfully")
        logger.info(f"[INIT] Ingester type: {type(_ingester)}")
        logger.info(f"[INIT] PipelineBuilder type: {type(_pipelineBuilder)}")
        
        # Test store connection
        store = _container.resolve("store")
        logger.info(f"[INIT] ✅ Store initialized: {type(store).__name__}")
        
        # Try to get initial count
        try:
            initial_count = store.count()
            logger.info(f"[INIT] ✅ Initial vector count: {initial_count}")
        except Exception as e:
            logger.warning(f"[INIT] ⚠️ Could not get initial count: {e}")
        
        logger.info("="*60)
        logger.info("[INIT] ✅ ALL COMPONENTS INITIALIZED SUCCESSFULLY")
        logger.info("="*60)
        return True
        
    except Exception as e:
        logger.error("="*60)
        logger.error("[INIT] ❌ FAILED TO INITIALIZE COMPONENTS")
        logger.error(f"[INIT] Error: {e}")
        logger.error("[INIT] Full traceback:")
        logger.error(traceback.format_exc())
        logger.error("="*60)
        
        # Create minimal components for health check
        _container = Container()
        _ingester = None
        _pipelineBuilder = None
        return False

# Create RAG router
logger.info("[ROUTER] Creating rag_router...")
rag_router = APIRouter(prefix="/api/rag", tags=["rag"])
logger.info(f"[ROUTER] rag_router created: {rag_router}")

@rag_router.get("/stats")
async def rag_stats() -> dict:
    """Get RAG system statistics including vector count"""
    logger.info("[API] GET /api/rag/stats called")
    
    if _container is None:
        logger.warning("[API] Container is None!")
        return {
            "total_vectors": 0,
            "namespace": "unknown",
            "store_type": "not_initialized",
            "status": "error",
            "error": "System not initialized"
        }
    
    try:
        store = _container.resolve("store")
        store_type = type(store).__name__
        logger.info(f"[API] Store type: {store_type}")
        
        vector_count = 0
        if hasattr(store, "count"):
            try:
                vector_count = store.count()
                logger.info(f"[API] Vector count: {vector_count}")
            except Exception as e:
                logger.error(f"[API] Error getting vector count: {e}")
        
        namespace = "default"
        if hasattr(store, "collection_name"):
            namespace = store.collection_name
        
        logger.info(f"[API] Returning stats: vectors={vector_count}, namespace={namespace}")
        return {
            "total_vectors": vector_count,
            "namespace": namespace,
            "store_type": store_type,
            "status": "ok"
        }
    except Exception as e:
        logger.error(f"[API] Failed to get RAG stats: {e}")
        logger.error(traceback.format_exc())
        return {
            "total_vectors": 0,
            "namespace": "unknown",
            "store_type": "unknown",
            "status": "error",
            "error": str(e)
        }

logger.info("[ROUTER] rag_router endpoints defined")

@app.on_event("startup")
async def startup_event():
    """Log startup information and initialize components"""
    logger.info("="*60)
    logger.info("[STARTUP] RAG Server Starting")
    logger.info("="*60)
    logger.info(f"[STARTUP] Working directory: {os.getcwd()}")
    logger.info(f"[STARTUP] Script location: {os.path.abspath(__file__)}")
    logger.info(f"[STARTUP] Python version: {sys.version}")
    
    # Log configuration
    store_config = config.get_section('store')
    logger.info(f"[STARTUP] Store type: {store_config.get('type')}")
    logger.info(f"[STARTUP] Persist directory (from config): {store_config.get('persist_directory')}")
    logger.info(f"[STARTUP] Collection name: {store_config.get('collection_name')}")
    
    # Initialize components
    logger.info("[STARTUP] Calling initialize_components()...")
    success = initialize_components()
    
    if success:
        logger.info("[STARTUP] ✅ All components initialized successfully")
    else:
        logger.error("[STARTUP] ⚠️ Some components failed to initialize")
        logger.error("[STARTUP] Server will run with limited functionality")
    
    logger.info("="*60)
    logger.info("[STARTUP] Startup sequence completed")
    logger.info("="*60)

# Include routers
logger.info("[APP] Including routers...")
try:
    logger.info("[APP] Including chunkers_router...")
    app.include_router(chunkers_router)
    logger.info("[APP] ✅ chunkers_router included successfully")
    
    logger.info("[APP] Including rag_router...")
    app.include_router(rag_router)  # RAG endpoints
    logger.info("[APP] ✅ rag_router included successfully")
    
    # Debug: List all routes
    logger.info("[APP] Registered routes:")
    for route in app.routes:
        if hasattr(route, 'path'):
            logger.info(f"[APP]   - {route.path}")
except Exception as e:
    logger.error(f"[APP] ❌ Failed to include routers: {e}")
    logger.error(traceback.format_exc())

# CORS configuration from config file
cors_config = config.get_section('cors')
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config.get('allow_origins', ["*"]),
    allow_credentials=cors_config.get('allow_credentials', True),
    allow_methods=cors_config.get('allow_methods', ["*"]),
    allow_headers=cors_config.get('allow_headers', ["*"]),
)

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

@app.get("/api/namespaces")
async def get_namespaces() -> List[dict]:
    """Get list of available namespaces/collections"""
    try:
        store = _container.resolve("store")
        if hasattr(store, 'list_namespaces'):
            namespaces = store.list_namespaces()
            return namespaces
        else:
            return [{"name": "default", "count": store.count()}]
    except Exception as e:
        logger.error(f"Failed to get namespaces: {e}")
        return []

@app.post("/api/switch_namespace")
async def switch_namespace(payload: dict) -> dict:
    """Switch to a different embedding model namespace"""
    try:
        model_name = payload.get("model_name")
        model_dim = payload.get("model_dim")
        
        store = _container.resolve("store")
        if hasattr(store, 'switch_namespace'):
            success = store.switch_namespace(model_name, model_dim)
            return {"success": success}
        else:
            return {"success": False, "error": "Store doesn't support namespaces"}
    except Exception as e:
        logger.error(f"Failed to switch namespace: {e}")
        return {"success": False, "error": str(e)}

@app.post("/ask", response_model=AskOut)
async def ask(body: AskIn) -> AskOut:
    rid = str(uuid.uuid4())
    t0 = time.time()
    
    try:
        policy = _container.resolve("policy")
        k = body.k if body.k is not None else policy.getDefaultcontext_chunk()

        # Create context with strict_mode as part of the question or handle it separately
        # Since RagContext doesn't have metadata, we'll handle strict_mode in the pipeline
        ctx = RagContext(
            question=body.question, k=k,
            expandedQueries=[], retrieved=[], reranked=[],
            compressedCtx="", prompt="", rawLlm="", parsed=None  # type: ignore
        )
        
        # Store strict_mode in a way that BuildPromptStep can access it
        # We'll pass it through the pipeline builder or modify the prompt directly
        
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

@app.get("/api/rerankers/types")
async def get_reranker_types() -> List[dict]:
    """Get available reranker types"""
    return [
        {
            "id": "cross-encoder",
            "name": "Cross Encoder",
            "description": "Neural network-based reranking using cross-encoder models",
            "models": [
                "cross-encoder/ms-marco-MiniLM-L-6-v2",
                "cross-encoder/ms-marco-MiniLM-L-12-v2",
                "cross-encoder/ms-marco-TinyBERT-L-2-v2"
            ]
        },
        {
            "id": "bm25",
            "name": "BM25",
            "description": "Classic probabilistic ranking function, fast and lightweight",
            "models": []
        },
        {
            "id": "colbert",
            "name": "ColBERT",
            "description": "Efficient retrieval via late interaction",
            "models": ["colbert-ir/colbertv2.0"]
        },
        {
            "id": "cohere",
            "name": "Cohere Rerank",
            "description": "Cloud-based reranking using Cohere API",
            "models": ["rerank-english-v2.0", "rerank-multilingual-v2.0"]
        },
        {
            "id": "simple",
            "name": "Simple Score",
            "description": "Basic scoring based on keyword matching",
            "models": []
        }
    ]

@app.get("/api/rerankers/current")
async def get_current_reranker() -> dict:
    """Get current reranker configuration"""  
    # Use the global config object
    reranker_config = config.get_section('pipeline').get('reranking', {})
    
    return {
        "type": reranker_config.get('type', 'cross-encoder'),
        "model": reranker_config.get('model', 'cross-encoder/ms-marco-MiniLM-L-6-v2'),
        "enabled": reranker_config.get('enabled', True),
        "context_chunk": reranker_config.get('context_chunk', 5)
    }

@app.post("/api/rerankers/update")
async def update_reranker(payload: dict) -> dict:
    """Update reranker configuration"""
    try:
        config_path = Path("config/config.yaml")
        # Load config from file
        with open(config_path, 'r', encoding='utf-8') as f:
            yaml_config = yaml.safe_load(f)
        
        # Update reranker settings
        if 'pipeline' not in yaml_config:
            yaml_config['pipeline'] = {}
        if 'reranking' not in yaml_config['pipeline']:
            yaml_config['pipeline']['reranking'] = {}
            
        reranker_config = yaml_config['pipeline']['reranking']
        
        if 'type' in payload:
            reranker_config['type'] = payload['type']
        if 'model' in payload:
            reranker_config['model'] = payload['model']
        if 'enabled' in payload:
            reranker_config['enabled'] = payload['enabled']
        if 'context_chunk' in payload:
            reranker_config['context_chunk'] = payload['context_chunk']
        
        # Save updated config
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_config, f, allow_unicode=True)
        
        # Rebuild container with new reranker
        global _container, _ingester, _pipelineBuilder
        rebuild_components()
        
        logger.info(f"Reranker updated to: {payload}")
        return {"success": True, "config": reranker_config}
        
    except Exception as e:
        logger.error(f"Failed to update reranker: {e}")
        raise HTTPException(status_code=500, detail=str(e))
