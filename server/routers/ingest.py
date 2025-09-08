"""
Ingest Router - Handles document ingestion endpoints with async processing
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import uuid

logger = logging.getLogger(__name__)

# Pydantic models for request/response
class DocumentIn(BaseModel):
    """Input model for a single document"""
    id: str
    title: str
    source: str
    text: str

class IngestRequest(BaseModel):
    """Request model for document ingestion"""
    documents: List[DocumentIn] = Field(min_items=1)
    batch_size: Optional[int] = Field(default=10, ge=1, le=100)
    
class IngestResponse(BaseModel):
    """Response model for document ingestion"""
    task_id: str
    status: str
    message: str
    document_count: int

class TaskStatusResponse(BaseModel):
    """Response model for task status"""
    task_id: str
    status: str
    progress: int
    total: int
    progress_percentage: float
    current_item: Optional[str]
    result: Optional[Dict[str, Any]]
    error: Optional[str]

# Global references (will be injected from main app)
_ingester = None
_task_manager = None

def set_ingester(ingester):
    """Set the ingester instance"""
    global _ingester
    _ingester = ingester

def set_task_manager(task_manager):
    """Set the task manager instance"""
    global _task_manager
    _task_manager = task_manager

# Create router
router = APIRouter(prefix="/api", tags=["ingest"])

@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents(payload: IngestRequest) -> IngestResponse:
    """
    Start async document ingestion task
    
    Args:
        payload: IngestRequest containing documents to ingest
        
    Returns:
        IngestResponse with task ID for tracking
    """
    logger.info(f"[INGEST] Received {len(payload.documents)} documents for async ingestion")
    
    if _ingester is None or _task_manager is None:
        logger.error("[INGEST] Services not initialized")
        raise HTTPException(
            status_code=503, 
            detail="Ingestion service not available"
        )
    
    try:
        # Convert documents to dict format
        documents = [
            {
                "id": doc.id,
                "title": doc.title,
                "source": doc.source,
                "text": doc.text
            }
            for doc in payload.documents
        ]
        
        # Import the async ingestion function
        from server.ingestion_service import async_ingest_documents
        
        # Create background task
        task_id = await _task_manager.create_task(
            task_type="ingest",
            task_func=async_ingest_documents,
            documents=documents,
            ingester=_ingester,
            batch_size=payload.batch_size or 10
        )
        
        logger.info(f"[INGEST] Created async task {task_id} for {len(documents)} documents")
        
        return IngestResponse(
            task_id=task_id,
            status="accepted",
            message=f"Ingestion task started. Use /api/ingest/status/{task_id} to track progress",
            document_count=len(documents)
        )
        
    except Exception as e:
        logger.error(f"[INGEST] Failed to start ingestion task: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start ingestion: {str(e)}"
        )

@router.get("/ingest/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """
    Get the status of an ingestion task
    
    Args:
        task_id: Task ID to check
        
    Returns:
        Current task status and progress
    """
    if _task_manager is None:
        raise HTTPException(
            status_code=503,
            detail="Task manager not available"
        )
    
    task_info = await _task_manager.get_task(task_id)
    
    if task_info is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )
    
    return TaskStatusResponse(
        task_id=task_info.id,
        status=task_info.status.value,
        progress=task_info.progress,
        total=task_info.total,
        progress_percentage=(task_info.progress / task_info.total * 100) if task_info.total > 0 else 0,
        current_item=task_info.current_item,
        result=task_info.result,
        error=task_info.error
    )

@router.get("/ingest/tasks")
async def get_all_tasks() -> List[Dict[str, Any]]:
    """
    Get all ingestion tasks
    
    Returns:
        List of all tasks with their status
    """
    if _task_manager is None:
        raise HTTPException(
            status_code=503,
            detail="Task manager not available"
        )
    
    tasks = await _task_manager.get_all_tasks()
    return [task.to_dict() for task in tasks]

@router.get("/ingest/tasks/active")
async def get_active_tasks() -> List[Dict[str, Any]]:
    """
    Get currently active ingestion tasks
    
    Returns:
        List of active tasks
    """
    if _task_manager is None:
        raise HTTPException(
            status_code=503,
            detail="Task manager not available"
        )
    
    tasks = await _task_manager.get_active_tasks()
    return [task.to_dict() for task in tasks]

@router.delete("/ingest/tasks/{task_id}")
async def cancel_task(task_id: str) -> dict:
    """
    Cancel a running ingestion task
    
    Args:
        task_id: Task ID to cancel
        
    Returns:
        Cancellation result
    """
    if _task_manager is None:
        raise HTTPException(
            status_code=503,
            detail="Task manager not available"
        )
    
    success = await _task_manager.cancel_task(task_id)
    
    if success:
        return {"success": True, "message": f"Task {task_id} cancelled"}
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found or not running"
        )

@router.get("/ingest/status")
async def get_ingest_status() -> dict:
    """Get the status of the ingestion service"""
    return {
        "service": "ingest",
        "status": "ready" if _ingester is not None and _task_manager is not None else "not_initialized",
        "ingester_type": type(_ingester).__name__ if _ingester else None,
        "task_manager": "available" if _task_manager else "not_available"
    }
