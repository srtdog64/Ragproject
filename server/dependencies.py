"""
Dependency Injection and Component Initialization
"""
import os
import logging
from typing import Tuple, Optional
from pathlib import Path

# Import all necessary components
from config_loader import config
from rag.di.container import Container
from rag.core.policy import Policy
from rag.adapters.llm_client import LlmFactory
from rag.adapters.embedders.manager import EmbedderManager
from rag.adapters.semantic_embedder import EmbedderFactory
from rag.stores.memory_store import InMemoryVectorStore
from rag.chunkers.registry import registry
from rag.chunkers.wrapper import ChunkerWrapper
from rag.retrievers.vector_retriever import VectorRetrieverImpl
from rag.ingest.ingester import Ingester
from rag.pipeline.builder import PipelineBuilder
from rag.rerankers.factory import RerankerFactory

logger = logging.getLogger(__name__)

def build_container() -> Container:
    """Build and configure the DI container"""
    c = Container()
    
    # Register config
    c.register("config", lambda _: config)
    
    # LLM configuration
    # LlmFactory.create() reads config internally, no need to pass config
    llm_instance = LlmFactory.create()
    c.register("llm", lambda _: llm_instance)
    
    # Embedder configuration
    embedder_config = config.get_section('embedder')
    default_embedder = None
    
    try:
        embedder_manager = EmbedderManager.fromYaml("config/embeddings.yml")
        c.register("embedder_manager", lambda _: embedder_manager)
        default_embedder = embedder_manager.getDefaultEmbedder()
        c.register("embedder", lambda _: default_embedder)
        logger.info("Embedder manager initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to load embedder manager: {e}")
        # Fallback to legacy factory
        try:
            default_embedder = EmbedderFactory.create(embedder_config)
            c.register("embedder", lambda _: default_embedder)
            logger.info("Using legacy embedder factory")
        except RuntimeError as e2:
            logger.error(f"CRITICAL ERROR: {e2}")
            raise
    
    # Create vector store
    store_config = config.get_section('store')
    store_type = store_config.get('type', 'memory')
    
    # Get embedder info for namespace
    embedding_model = None
    embedding_dim = None
    
    if default_embedder:
        if hasattr(default_embedder, 'model_name'):
            embedding_model = default_embedder.model_name
        if hasattr(default_embedder, 'dimension'):
            embedding_dim = default_embedder.dimension
    
    if store_type == 'chroma':
        from rag.stores.chroma_store import ChromaVectorStore
        persist_dir = store_config.get('persist_directory', './chroma_db')
        
        # Handle relative and absolute paths
        if not os.path.isabs(persist_dir):
            project_root = Path(__file__).parent.parent
            persist_dir = str(project_root / persist_dir)
        
        persist_dir = os.path.normpath(persist_dir)
        collection = store_config.get('collection_name', 'rag_documents')
        
        logger.info(f"ChromaDB persist_directory: {persist_dir}")
        logger.info(f"Directory exists: {os.path.exists(persist_dir)}")
        
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
    else:
        # Default to in-memory store
        store_instance = InMemoryVectorStore()
        logger.info("Using in-memory vector store")
    
    c.register("store", lambda _: store_instance)
    
    # Register retriever with embedder
    retriever = VectorRetrieverImpl(store_instance, default_embedder)
    c.register("retriever", lambda _: retriever)
    
    # Register chunker
    chunker_config = config.get_section('chunker')
    default_strategy = chunker_config.get('default_strategy', 'adaptive')
    logger.info(f"Chunker registry initialized with strategy: {default_strategy}")
    
    # ChunkerRegistry uses get_chunker, not getStrategy
    try:
        chunker = registry.get_chunker(default_strategy)
        registry.set_current_strategy(default_strategy)
    except:
        # Fallback to any available strategy
        logger.warning(f"Strategy '{default_strategy}' not found, using default")
        chunker = registry.get_chunker()
    
    # ChunkerWrapper doesn't take arguments
    wrapper = ChunkerWrapper()
    c.register("chunker", lambda _: wrapper)
    
    # Register reranker
    pipeline_config = config.get_section('pipeline')
    if pipeline_config:
        reranker_config = pipeline_config.get('reranking', {})
    else:
        reranker_config = {}
    reranker_type = reranker_config.get('type', 'simple')
    reranker = RerankerFactory.create(reranker_type)
    c.register("reranker", lambda _: reranker)
    
    # Register policy
    pipeline_config = config.get_section('pipeline')
    # Policy only accepts maxContextChars and defaultcontext_chunk
    policy_params = {}
    if pipeline_config:
        if 'max_context_chars' in pipeline_config:
            policy_params['maxContextChars'] = pipeline_config['max_context_chars']
        if 'default_top_k' in pipeline_config:
            policy_params['defaultcontext_chunk'] = pipeline_config['default_top_k']
    policy = Policy(**policy_params) if policy_params else Policy()
    c.register("policy", lambda _: policy)
    
    return c

def build_pipeline(container: Container) -> Tuple:
    """Build the ingester and pipeline builder"""
    # Create ingester
    ingester = Ingester(
        chunker=container.resolve("chunker"),
        embedder=container.resolve("embedder"),
        store=container.resolve("store")
    )
    logger.info("Ingester created successfully")
    
    # Create pipeline builder - does not take container as argument
    pipeline_builder = PipelineBuilder()
    logger.info("PipelineBuilder created successfully")
    
    return ingester, pipeline_builder

def initialize_components() -> Tuple[Container, Ingester, PipelineBuilder]:
    """Initialize all components and return them"""
    try:
        logger.info("Initializing RAG components...")
        
        # Build container
        container = build_container()
        logger.info("Container built successfully")
        
        # Build pipeline components
        ingester, pipeline_builder = build_pipeline(container)
        logger.info("Pipeline components built successfully")
        
        # Test store connection
        store = container.resolve("store")
        logger.info(f"Store initialized: {type(store).__name__}")
        
        return container, ingester, pipeline_builder
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

# Dependency injection functions for FastAPI
_container: Optional[Container] = None
_ingester: Optional[Ingester] = None
_pipeline_builder: Optional[PipelineBuilder] = None

def get_container() -> Container:
    """Get the DI container instance"""
    if _container is None:
        raise RuntimeError("Container not initialized")
    return _container

def get_ingester() -> Ingester:
    """Get the ingester instance"""
    if _ingester is None:
        raise RuntimeError("Ingester not initialized")
    return _ingester

def get_pipeline_builder() -> PipelineBuilder:
    """Get the pipeline builder instance"""
    if _pipeline_builder is None:
        raise RuntimeError("PipelineBuilder not initialized")
    return _pipeline_builder

def set_global_components(container: Container, ingester: Ingester, pipeline_builder: PipelineBuilder):
    """Set global component instances"""
    global _container, _ingester, _pipeline_builder
    _container = container
    _ingester = ingester
    _pipeline_builder = pipeline_builder
