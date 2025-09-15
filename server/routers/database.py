"""
Database management endpoints
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/database", tags=["database"])

# Global container reference (will be set by main.py)
_container = None

def set_container(container):
    """Set the container instance"""
    global _container
    _container = container

def get_container():
    """Get the container instance"""
    if _container is None:
        raise HTTPException(status_code=500, detail="Container not initialized")
    return _container

@router.post("/clear")
async def clear_database(container = Depends(get_container)):
    """
    Clear all data from the vector database
    
    This will permanently delete all vectors and documents from the current collection.
    """
    try:
        # Get the vector store from container
        store = container.resolve("store")
        
        if not store:
            raise HTTPException(status_code=500, detail="Vector store not available")
        
        # Get count before clearing
        initial_count = 0
        try:
            if hasattr(store, "count"):
                initial_count = store.count()
        except Exception as e:
            logger.warning(f"Could not get initial count: {e}")
        
        # Clear the database
        if hasattr(store, "clear"):
            store.clear()
            logger.info(f"Database cleared successfully. Removed {initial_count} documents")
        else:
            raise HTTPException(status_code=500, detail="Store does not support clear operation")
        
        # Get count after clearing to verify
        final_count = 0
        try:
            if hasattr(store, "count"):
                final_count = store.count()
        except Exception as e:
            logger.warning(f"Could not get final count: {e}")
        
        return {
            "success": True,
            "message": f"Database cleared successfully. Removed {initial_count} documents",
            "initial_count": initial_count,
            "final_count": final_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear database: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear database: {str(e)}")

@router.get("/stats")
async def get_database_stats(container = Depends(get_container)):
    """
    Get database statistics
    """
    try:
        # Get the vector store from container
        store = container.resolve("store")
        
        if not store:
            raise HTTPException(status_code=500, detail="Vector store not available")
        
        stats = {}
        
        # Get document count
        try:
            if hasattr(store, "count"):
                stats["total_vectors"] = store.count()
            else:
                stats["total_vectors"] = 0
        except Exception as e:
            logger.warning(f"Could not get document count: {e}")
            stats["total_vectors"] = 0
        
        # Get namespaces if available
        try:
            if hasattr(store, "list_namespaces"):
                namespaces = store.list_namespaces()
                stats["namespaces"] = len(namespaces)
                stats["namespace_details"] = namespaces
            else:
                stats["namespaces"] = 1  # Default collection
                stats["namespace_details"] = []
        except Exception as e:
            logger.warning(f"Could not get namespaces: {e}")
            stats["namespaces"] = 1
            stats["namespace_details"] = []
        
        # Get current collection name if available
        try:
            if hasattr(store, "collection_name"):
                stats["current_collection"] = store.collection_name
            else:
                stats["current_collection"] = "default"
        except Exception as e:
            stats["current_collection"] = "unknown"
        
        # Get store type
        stats["store_type"] = store.__class__.__name__
        
        return {
            "success": True,
            "stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get database stats: {str(e)}")

@router.get("/health")
async def check_database_health(container = Depends(get_container)):
    """
    Check database health and connectivity
    """
    try:
        # Get the vector store from container
        store = container.resolve("store")
        
        if not store:
            return {
                "success": False,
                "healthy": False,
                "message": "Vector store not available",
                "details": {}
            }
        
        health_info = {
            "store_type": store.__class__.__name__,
            "available": True
        }
        
        # Test basic operations
        try:
            # Try to get count
            if hasattr(store, "count"):
                count = store.count()
                health_info["document_count"] = count
                health_info["count_accessible"] = True
            else:
                health_info["count_accessible"] = False
                
            # Test if collection exists (for ChromaDB)
            if hasattr(store, "collection") and store.collection:
                health_info["collection_accessible"] = True
                if hasattr(store, "collection_name"):
                    health_info["collection_name"] = store.collection_name
            else:
                health_info["collection_accessible"] = False
                
        except Exception as e:
            health_info["error"] = str(e)
            health_info["fully_functional"] = False
        
        is_healthy = health_info.get("available", False) and health_info.get("count_accessible", False)
        
        return {
            "success": True,
            "healthy": is_healthy,
            "message": "Database health check completed",
            "details": health_info
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "success": False,
            "healthy": False,
            "message": f"Database health check failed: {str(e)}",
            "details": {}
        }
