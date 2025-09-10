"""
Main FastAPI Application
Clean server architecture with separated routers
"""
import os
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import routers
from server.routers import health, rag, ingest, ask, namespaces, config
from rag.chunkers.api_router import router as chunkers_router

# Import task manager
from server.tasks import get_task_manager

# Import dependencies
from config_loader import config as app_config
from server.dependencies import (
    initialize_components,
    get_container,
    get_ingester,
    get_pipeline_builder
)

# Global components (will be initialized on startup)
_container = None
_ingester = None
_pipeline_builder = None

def rebuild_components():
    """Rebuild components after configuration change"""
    global _container, _ingester, _pipeline_builder
    try:
        logger.info("Rebuilding components after config change...")
        _container, _ingester, _pipeline_builder = initialize_components()
        
        # Update all routers with new components
        rag.set_container(_container)
        ingest.set_ingester(_ingester)
        ask.set_pipeline_builder(_pipeline_builder)
        ask.set_container(_container)
        namespaces.set_container(_container)
        
        logger.info("Components rebuilt successfully")
    except Exception as e:
        logger.error(f"Failed to rebuild components: {e}")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    global _container, _ingester, _pipeline_builder
    
    # Startup
    logger.info("="*60)
    logger.info("Starting RAG Server")
    logger.info("="*60)
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Script location: {os.path.abspath(__file__)}")
    
    # Initialize task manager
    task_manager = get_task_manager()
    logger.info("Task manager initialized")
    
    # Initialize components
    try:
        _container, _ingester, _pipeline_builder = initialize_components()
        logger.info("All components initialized successfully")
        
        # Set components for routers
        rag.set_container(_container)
        ingest.set_ingester(_ingester)
        ingest.set_task_manager(task_manager)  # Set task manager for async ingestion
        ask.set_pipeline_builder(_pipeline_builder)
        ask.set_container(_container)
        namespaces.set_container(_container)
        config.set_config(app_config)
        config.set_rebuild_callback(rebuild_components)
        
        # Log initial stats
        try:
            store = _container.resolve("store")
            if hasattr(store, "count"):
                count = store.count()
                logger.info(f"Initial vector count: {count}")
        except Exception as e:
            logger.warning(f"Could not get initial count: {e}")
            
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Set None values to prevent errors
        rag.set_container(None)
        ingest.set_ingester(None)
        ask.set_pipeline_builder(None)
        ask.set_container(None)
        namespaces.set_container(None)
    
    # Log registered routes after everything is set up
    logger.info("Registered routes:")
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            methods = ', '.join(route.methods) if route.methods else 'ANY'
            logger.info(f"  {route.path} [{methods}]")
    
    logger.info("="*60)
    logger.info("Server started successfully")
    logger.info("="*60)
    
    yield  # Server runs here
    
    # Shutdown
    logger.info("Shutting down server...")

# Create FastAPI app with lifespan manager
app = FastAPI(
    title="RAG Service with Gemini",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
cors_config = app_config.get_section('cors')
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config.get('allow_origins', ["*"]),
    allow_credentials=cors_config.get('allow_credentials', True),
    allow_methods=cors_config.get('allow_methods', ["*"]),
    allow_headers=cors_config.get('allow_headers', ["*"]),
)

# Include all routers
app.include_router(health.router)      # /health endpoints
app.include_router(rag.router)         # /api/rag/* endpoints
app.include_router(ingest.router)      # /api/ingest endpoints
app.include_router(ask.router)         # /api/ask endpoints
app.include_router(namespaces.router)  # /api/namespaces endpoints
app.include_router(config.router)      # /api/config/* endpoints
app.include_router(chunkers_router)    # /api/chunkers/* endpoints

if __name__ == "__main__":
    import uvicorn
    from config_loader import config as app_config
    
    # Get server config
    server_config = app_config.get_section('server')
    host = server_config.get('host', '127.0.0.1')
    port = server_config.get('port', 7001)
    
    uvicorn.run(
        "server.main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
