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
from rerankers.factory import RerankerFactory
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
        defaultTopK=policy_config.get('defaultTopK', 5)
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
        print("✅ Embedder manager initialized successfully")
    except Exception as e:
        print(f"⚠️ Warning: Failed to load embedder manager: {e}")
        # Fallback to old factory method
        try:
            default_embedder = EmbedderFactory.create(embedder_config)
            c.register("embedder", lambda _: default_embedder)
            print("✅ Using legacy embedder factory")
        except RuntimeError as e2:
            print(f"❌ CRITICAL ERROR: {e2}")
            print("The system cannot function without a proper embedder.")
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
        from stores.chroma_store import ChromaVectorStore
        persist_dir = store_config.get('persist_directory', './chroma_db')
        collection = store_config.get('collection_name', 'rag_documents')
        store_instance = ChromaVectorStore(
            persist_directory=persist_dir,
            collection_name=collection,
            embedding_model=embedding_model,
            embedding_dim=embedding_dim
        )
        logger.info(f"Using ChromaDB vector store (persistent) at {persist_dir}")
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

@app.get("/api/rag/stats")
async def get_rag_stats() -> dict:
    """Get RAG system statistics including vector count"""
    try:
        store = _container.resolve("store")
        
        # Get vector count - ensure we're calling the right method
        vector_count = 0
        if hasattr(store, 'count'):
            vector_count = store.count()
            logger.info(f"Vector count from store: {vector_count}")
        elif hasattr(store, 'collection') and hasattr(store.collection, 'count'):
            # For ChromaDB, might need to call collection.count() directly
            vector_count = store.collection.count()
            logger.info(f"Vector count from collection: {vector_count}")
        else:
            logger.warning("Store doesn't have a count method")
        
        # Get current namespace
        namespace = "default"
        if hasattr(store, 'collection_name'):
            namespace = store.collection_name
        elif hasattr(store, 'namespace_manager') and hasattr(store.namespace_manager, 'current_namespace'):
            namespace = store.namespace_manager.current_namespace
        
        logger.info(f"RAG Stats: {vector_count} vectors in namespace '{namespace}'")
        
        return {
            "total_vectors": vector_count,
            "namespace": namespace,
            "status": "ok"
        }
    except Exception as e:
        logger.error(f"Failed to get RAG stats: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "total_vectors": 0,
            "namespace": "unknown",
            "status": "error",
            "error": str(e)
        }

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
        k = body.k if body.k is not None else policy.getDefaultTopK()

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
        "topK": reranker_config.get('topK', 5)
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
        if 'topK' in payload:
            reranker_config['topK'] = payload['topK']
        
        # Save updated config
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_config, f, allow_unicode=True)
        
        # Rebuild container with new reranker
        global _container, _ingester, _pipelineBuilder
        _container, _ingester, _pipelineBuilder = initializeComponents(config)
        
        logger.info(f"Reranker updated to: {payload}")
        return {"success": True, "config": reranker_config}
        
    except Exception as e:
        logger.error(f"Failed to update reranker: {e}")
        raise HTTPException(status_code=500, detail=str(e))
