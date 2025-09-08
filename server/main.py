"""
Main FastAPI Application
Clean server architecture with separated routers
"""
import os
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
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
from server.routers import health, rag
from rag.chunkers.api_router import router as chunkers_router

# Import dependencies
from config_loader import config
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
    
    # Initialize components
    try:
        _container, _ingester, _pipeline_builder = initialize_components()
        logger.info("All components initialized successfully")
        
        # Set container for routers that need it
        rag.set_container(_container)
        
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
        # Even if initialization fails, set None container to prevent 404 errors
        rag.set_container(None)
    
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
cors_config = config.get_section('cors')
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config.get('allow_origins', ["*"]),
    allow_credentials=cors_config.get('allow_credentials', True),
    allow_methods=cors_config.get('allow_methods', ["*"]),
    allow_headers=cors_config.get('allow_headers', ["*"]),
)

# Include routers
logger.info("Registering routers...")
app.include_router(health.router)
app.include_router(rag.router)
app.include_router(chunkers_router)

# Log registered routes
logger.info("Registered routes:")
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        methods = ', '.join(route.methods) if route.methods else 'ANY'
        logger.info(f"  {route.path} [{methods}]")

# Additional endpoints can be added here if needed
@app.post("/ingest")
async def ingest(payload: dict) -> dict:
    """Document ingestion endpoint"""
    if _ingester is None:
        raise HTTPException(status_code=503, detail="Ingester not initialized")
    
    # Implementation will be moved to separate router
    return {"status": "ok", "message": "Ingestion endpoint"}

@app.post("/ask")
async def ask(question: str) -> dict:
    """Query endpoint"""
    if _pipeline_builder is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    # Implementation will be moved to separate router
    return {"status": "ok", "question": question}

@app.get("/api/namespaces")
async def get_namespaces() -> list:
    """Get available namespaces"""
    if _container is None:
        return []
    
    # Implementation will be moved to separate router
    return ["default", "rag_documents"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server.main:app",
        host="0.0.0.0",
        port=7001,
        reload=True,
        log_level="info"
    )
