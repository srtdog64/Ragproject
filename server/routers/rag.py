"""
RAG Router - Handles all RAG-related endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# This will be injected from main app
_container = None

def set_container(container):
    """Set the DI container instance"""
    global _container
    _container = container

# Create router
router = APIRouter(prefix="/api/rag", tags=["rag"])

@router.get("/stats")
async def get_rag_stats() -> dict:
    """Get RAG system statistics including vector count"""
    logger.info("[RAG API] /stats endpoint called")
    
    if _container is None:
        logger.error("[RAG API] Container not initialized")
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
        logger.info(f"[RAG API] Store type: {store_type}")
        
        # Get vector count
        vector_count = 0
        if hasattr(store, "count"):
            try:
                vector_count = store.count()
                logger.info(f"[RAG API] Vector count: {vector_count}")
            except Exception as e:
                logger.error(f"[RAG API] Error getting count: {e}")
        
        # Get namespace and collection info
        namespace = "default"
        actual_collection = "unknown"
        base_collection = "unknown"
        
        if hasattr(store, "collection_name"):
            actual_collection = store.collection_name
            namespace = actual_collection  # Use full collection name as namespace
        
        if hasattr(store, "base_collection_name"):
            base_collection = store.base_collection_name
        elif hasattr(store, "namespace"):
            namespace = store.namespace
        
        logger.info(f"[RAG API] Returning stats: vectors={vector_count}, namespace={namespace}")
        
        result = {
            "total_vectors": vector_count,
            "namespace": namespace,
            "store_type": store_type,
            "status": "ok"
        }
        
        # Add additional collection info if available
        if actual_collection != "unknown":
            result["collection_name"] = actual_collection
        if base_collection != "unknown":
            result["base_collection"] = base_collection
            
        return result
        
    except Exception as e:
        logger.error(f"[RAG API] Failed to get stats: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "total_vectors": 0,
            "namespace": "unknown",
            "store_type": "error",
            "status": "error",
            "error": str(e)
        }

@router.get("/collections")
async def get_collections() -> dict:
    """Get all available collections/namespaces"""
    logger.info("[RAG API] /collections endpoint called")
    
    if _container is None:
        return {"collections": [], "error": "System not initialized"}
    
    try:
        store = _container.resolve("store")
        
        # Try to get collections from ChromaDB
        if hasattr(store, "client"):
            collections = store.client.list_collections()
            collection_info = []
            
            for coll in collections:
                try:
                    count = coll.count()
                    collection_info.append({
                        "name": coll.name,
                        "count": count,
                        "metadata": coll.metadata if hasattr(coll, "metadata") else {}
                    })
                except Exception as e:
                    logger.error(f"Error getting info for collection {coll.name}: {e}")
                    collection_info.append({
                        "name": coll.name,
                        "count": 0,
                        "error": str(e)
                    })
            
            return {"collections": collection_info, "status": "ok"}
        else:
            return {"collections": [], "status": "not_supported"}
            
    except Exception as e:
        logger.error(f"[RAG API] Failed to get collections: {e}")
        return {"collections": [], "error": str(e)}
