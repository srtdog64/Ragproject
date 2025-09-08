"""
Namespaces Router - Handles namespace/collection management
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Pydantic models
class NamespaceInfo(BaseModel):
    """Information about a namespace/collection"""
    name: str
    count: int
    metadata: Dict[str, Any] = {}
    model: Optional[str] = None
    dimension: Optional[int] = None

class SwitchNamespaceRequest(BaseModel):
    """Request to switch to a different namespace"""
    model_name: str
    model_dim: Optional[int] = None

class SwitchNamespaceResponse(BaseModel):
    """Response for namespace switch"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None

# Global reference to container
_container = None

def set_container(container):
    """Set the DI container instance"""
    global _container
    _container = container

# Create router
router = APIRouter(prefix="/api", tags=["namespaces"])

@router.get("/namespaces", response_model=List[NamespaceInfo])
async def get_namespaces() -> List[NamespaceInfo]:
    """
    Get list of available namespaces/collections
    
    Returns:
        List of namespace information
    """
    logger.info("[NAMESPACES] Getting list of namespaces")
    
    if _container is None:
        logger.error("[NAMESPACES] Container not initialized")
        return []
    
    try:
        store = _container.resolve("store")
        
        # Check if store supports namespaces
        if hasattr(store, 'list_namespaces'):
            namespaces = store.list_namespaces()
            
            # Convert to NamespaceInfo objects
            result = []
            for ns in namespaces:
                if isinstance(ns, dict):
                    info = NamespaceInfo(
                        name=ns.get('name', 'unknown'),
                        count=ns.get('count', 0),
                        metadata=ns.get('metadata', {}),
                        model=ns.get('model'),
                        dimension=ns.get('dimension')
                    )
                    result.append(info)
                else:
                    # Handle simple namespace format
                    info = NamespaceInfo(
                        name=str(ns),
                        count=0,
                        metadata={}
                    )
                    result.append(info)
            
            logger.info(f"[NAMESPACES] Found {len(result)} namespaces")
            return result
            
        else:
            # Store doesn't support multiple namespaces
            # Return current namespace/collection
            count = 0
            if hasattr(store, 'count'):
                try:
                    count = store.count()
                except:
                    pass
            
            namespace_name = "default"
            if hasattr(store, 'collection_name'):
                namespace_name = store.collection_name
            elif hasattr(store, 'namespace'):
                namespace_name = store.namespace
            
            logger.info(f"[NAMESPACES] Single namespace: {namespace_name}")
            
            return [
                NamespaceInfo(
                    name=namespace_name,
                    count=count,
                    metadata={"type": type(store).__name__}
                )
            ]
            
    except Exception as e:
        logger.error(f"[NAMESPACES] Failed to get namespaces: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

@router.post("/switch_namespace", response_model=SwitchNamespaceResponse)
async def switch_namespace(request: SwitchNamespaceRequest) -> SwitchNamespaceResponse:
    """
    Switch to a different embedding model namespace
    
    Args:
        request: Namespace switch request with model information
        
    Returns:
        Success status and message
    """
    logger.info(f"[NAMESPACES] Switch request: model={request.model_name}, dim={request.model_dim}")
    
    if _container is None:
        logger.error("[NAMESPACES] Container not initialized")
        return SwitchNamespaceResponse(
            success=False,
            error="Service not initialized"
        )
    
    try:
        store = _container.resolve("store")
        
        # Check if store supports namespace switching
        if hasattr(store, 'switch_namespace'):
            success = store.switch_namespace(
                request.model_name,
                request.model_dim
            )
            
            if success:
                logger.info(f"[NAMESPACES] Successfully switched to {request.model_name}")
                return SwitchNamespaceResponse(
                    success=True,
                    message=f"Switched to namespace for model: {request.model_name}"
                )
            else:
                logger.error(f"[NAMESPACES] Failed to switch to {request.model_name}")
                return SwitchNamespaceResponse(
                    success=False,
                    error=f"Failed to switch to namespace for model: {request.model_name}"
                )
        else:
            logger.warning("[NAMESPACES] Store doesn't support namespace switching")
            return SwitchNamespaceResponse(
                success=False,
                error="Store doesn't support namespace switching"
            )
            
    except Exception as e:
        logger.error(f"[NAMESPACES] Failed to switch namespace: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return SwitchNamespaceResponse(
            success=False,
            error=str(e)
        )

@router.delete("/namespaces/{namespace_name}")
async def delete_namespace(namespace_name: str) -> dict:
    """
    Delete a specific namespace/collection
    
    Args:
        namespace_name: Name of the namespace to delete
        
    Returns:
        Success status
    """
    logger.info(f"[NAMESPACES] Delete request for: {namespace_name}")
    
    if _container is None:
        raise HTTPException(
            status_code=503,
            detail="Service not initialized"
        )
    
    try:
        store = _container.resolve("store")
        
        # For ChromaDB, we can delete collections
        if hasattr(store, 'client'):
            try:
                store.client.delete_collection(name=namespace_name)
                logger.info(f"[NAMESPACES] Deleted namespace: {namespace_name}")
                return {"success": True, "message": f"Deleted namespace: {namespace_name}"}
            except Exception as e:
                logger.error(f"[NAMESPACES] Failed to delete: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to delete namespace: {str(e)}"
                )
        else:
            raise HTTPException(
                status_code=501,
                detail="Store doesn't support namespace deletion"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[NAMESPACES] Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
