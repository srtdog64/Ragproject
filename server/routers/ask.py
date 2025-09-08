"""
Ask Router - Handles query/question endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import logging
import uuid
import time

logger = logging.getLogger(__name__)

# Pydantic models
class AskRequest(BaseModel):
    """Request model for asking questions"""
    question: str = Field(min_length=1, max_length=10000)
    k: Optional[int] = Field(default=None, ge=1, le=100)
    provider: Optional[str] = Field(default=None)
    model: Optional[str] = Field(default=None)
    strict_mode: Optional[bool] = Field(default=False)
    
    class Config:
        protected_namespaces = ()  # Disable protected namespace check

class AskResponse(BaseModel):
    """Response model for questions"""
    answer: str
    ctxIds: List[str]
    requestId: str
    latencyMs: int
    status: str = "success"

# Global references
_pipeline_builder = None
_container = None

def set_pipeline_builder(builder):
    """Set the pipeline builder instance"""
    global _pipeline_builder
    _pipeline_builder = builder

def set_container(container):
    """Set the DI container instance"""
    global _container
    _container = container

# Create router
router = APIRouter(prefix="/api", tags=["query"])

@router.post("/ask", response_model=AskResponse)
async def ask_question(body: AskRequest) -> AskResponse:
    """
    Process a question through the RAG pipeline
    
    Args:
        body: AskRequest containing the question and parameters
        
    Returns:
        AskResponse with the answer and metadata
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    logger.info(f"[ASK] Request {request_id}: '{body.question[:100]}...'")
    
    if _pipeline_builder is None or _container is None:
        logger.error("[ASK] Pipeline not initialized")
        raise HTTPException(
            status_code=503,
            detail="Query service not available"
        )
    
    try:
        # Get policy for default k value
        policy = _container.resolve("policy")
        k = body.k if body.k is not None else policy.getDefaultcontext_chunk()
        
        logger.debug(f"[ASK] Using k={k} for retrieval")
        
        # Create RAG context
        from rag.core.types import RagContext
        
        ctx = RagContext(
            question=body.question,
            k=k,
            expandedQueries=[],
            retrieved=[],
            reranked=[],
            compressedCtx="",
            prompt="",
            rawLlm="",
            parsed=None
        )
        
        # Handle provider/model override if specified
        if body.provider or body.model:
            logger.info(f"[ASK] Using custom LLM: provider={body.provider}, model={body.model}")
            # This would require modifying the LLM instance in the container
            # For now, we'll use the default configured LLM
        
        # Build and run pipeline
        logger.debug(f"[ASK] Building pipeline for request {request_id}")
        pipeline = _pipeline_builder.build()
        
        logger.debug(f"[ASK] Running pipeline for request {request_id}")
        result = await pipeline.run(ctx)
        
        # Check result
        if result.isErr():
            error_msg = str(result.getError())
            logger.error(f"[ASK] Pipeline error for request {request_id}: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=f"Pipeline error: {error_msg}"
            )
        
        # Get the answer
        answer = result.getValue()
        
        # Extract context IDs from retrieved chunks
        ctx_ids = []
        if hasattr(ctx, 'retrieved') and ctx.retrieved:
            ctx_ids = [chunk.chunk.id for chunk in ctx.retrieved[:5]]  # Top 5 context IDs
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        logger.info(f"[ASK] Request {request_id} completed in {latency_ms}ms")
        
        # Format response based on parsed result type
        response_text = ""
        if hasattr(answer, 'text'):
            response_text = answer.text
        elif hasattr(answer, 'getValue'):
            response_text = answer.getValue()
        elif isinstance(answer, str):
            response_text = answer
        else:
            response_text = str(answer)
        
        return AskResponse(
            answer=response_text,
            ctxIds=ctx_ids,
            requestId=request_id,
            latencyMs=latency_ms,
            status="success"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ASK] Unexpected error for request {request_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Calculate latency even for errors
        latency_ms = int((time.time() - start_time) * 1000)
        
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/ask/status")
async def get_ask_status() -> dict:
    """Get the status of the query service"""
    return {
        "service": "ask",
        "status": "ready" if _pipeline_builder is not None else "not_initialized",
        "pipeline_builder": type(_pipeline_builder).__name__ if _pipeline_builder else None,
        "container": "initialized" if _container else "not_initialized"
    }
