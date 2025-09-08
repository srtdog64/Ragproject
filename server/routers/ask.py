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
    retrievedCount: int = 0  # Number of documents retrieved from vector store
    rerankedCount: int = 0   # Number of documents after reranking

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
        k = body.k if body.k is not None else policy.getDefaulttopK()
        
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
        
        if _pipeline_builder is None:
            logger.error(f"[ASK] Pipeline builder is None!")
            raise HTTPException(
                status_code=503,
                detail="Pipeline builder not initialized"
            )
        
        pipeline = _pipeline_builder.build()
        
        if pipeline is None:
            logger.error(f"[ASK] Built pipeline is None!")
            raise HTTPException(
                status_code=503,
                detail="Pipeline build failed"
            )
        
        logger.debug(f"[ASK] Running pipeline for request {request_id}")
        logger.debug(f"[ASK] Context question: {ctx.question[:100]}...")
        logger.debug(f"[ASK] Context k: {ctx.k}")
        
        try:
            result = await pipeline.run(ctx)
            logger.debug(f"[ASK] Pipeline execution completed for {request_id}")
        except Exception as e:
            logger.error(f"[ASK] Pipeline execution error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Pipeline execution failed: {str(e)}"
            )
        
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
        logger.debug(f"[ASK] Raw answer type: {type(answer)}")
        logger.debug(f"[ASK] Raw answer: {str(answer)[:200]}...")
        
        # Initialize counts
        retrieved_count = 0
        reranked_count = 0
        ctx_ids = []
        
        # Get rerank_k limit from config (this is the final context size)
        from config_loader import config as app_config
        retrieval_config = app_config.get_section('retrieval')
        rerank_k = retrieval_config.get('rerank_k', 5) if retrieval_config else 5
        
        # First check if we have metadata from parsed answer (e.g., from a parser that adds metadata)
        if hasattr(answer, 'metadata') and answer.metadata:
            ctx_ids = answer.metadata.get('ctxIds', [])
            # Apply limit
            ctx_ids = ctx_ids[:rerank_k]
            
            # If we got ctxIds from metadata, assume they're from reranked
            # Count based on what's available in the context
            if hasattr(ctx, 'retrieved') and ctx.retrieved:
                retrieved_count = len(ctx.retrieved)
            if hasattr(ctx, 'reranked') and ctx.reranked:
                reranked_count = len(ctx.reranked)
            else:
                # If no reranked, the ctxIds are the final context count
                reranked_count = len(ctx_ids)
            
            logger.debug(f"[ASK] Got {len(ctx_ids)} context IDs from answer.metadata")
        
        # If not available from metadata, get from context
        if not ctx_ids:
            # Count documents
            if hasattr(ctx, 'retrieved') and ctx.retrieved:
                retrieved_count = len(ctx.retrieved)
            if hasattr(ctx, 'reranked') and ctx.reranked:
                reranked_count = len(ctx.reranked)
                ctx_ids = [chunk.chunk.id for chunk in ctx.reranked[:rerank_k]]
                logger.debug(f"[ASK] Got {len(ctx_ids)} context IDs from ctx.reranked")
            elif hasattr(ctx, 'retrieved') and ctx.retrieved:
                # No reranking, use retrieved directly
                ctx_ids = [chunk.chunk.id for chunk in ctx.retrieved[:rerank_k]]
                reranked_count = len(ctx_ids)  # Final context is what we're showing
                logger.debug(f"[ASK] Got {len(ctx_ids)} context IDs from ctx.retrieved")
        
        logger.info(f"[ASK] Retrieved: {retrieved_count}, Reranked: {reranked_count}, Context IDs: {len(ctx_ids)}")
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        logger.info(f"[ASK] Request {request_id} completed in {latency_ms}ms")
        
        # Format response based on parsed result type
        response_text = ""
        if answer is None:
            logger.error(f"[ASK] Answer is None!")
            response_text = "Error: No answer generated"
        elif hasattr(answer, 'text'):
            response_text = answer.text
            logger.debug(f"[ASK] Using answer.text: {response_text[:100]}...")
        elif hasattr(answer, 'getValue'):
            response_text = answer.getValue()
            logger.debug(f"[ASK] Using answer.getValue(): {response_text[:100]}...")
        elif isinstance(answer, str):
            response_text = answer
            logger.debug(f"[ASK] Using string answer: {response_text[:100]}...")
        else:
            response_text = str(answer)
            logger.debug(f"[ASK] Using str(answer): {response_text[:100]}...")
        
        return AskResponse(
            answer=response_text,
            ctxIds=ctx_ids,
            requestId=request_id,
            latencyMs=latency_ms,
            status="success",
            retrievedCount=retrieved_count,
            rerankedCount=reranked_count
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
