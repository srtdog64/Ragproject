"""
Ingest Router - Handles document ingestion endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
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
    
class IngestResponse(BaseModel):
    """Response model for document ingestion"""
    ingestedChunks: int
    documentCount: int
    status: str
    message: Optional[str] = None

# Global references (will be injected from main app)
_ingester = None

def set_ingester(ingester):
    """Set the ingester instance"""
    global _ingester
    _ingester = ingester

# Create router
router = APIRouter(prefix="/api", tags=["ingest"])

@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents(payload: IngestRequest) -> IngestResponse:
    """
    Ingest documents into the RAG system
    
    Args:
        payload: IngestRequest containing documents to ingest
        
    Returns:
        IngestResponse with ingestion results
    """
    logger.info(f"[INGEST] Received {len(payload.documents)} documents for ingestion")
    
    if _ingester is None:
        logger.error("[INGEST] Ingester not initialized")
        raise HTTPException(
            status_code=503, 
            detail="Ingester service not available"
        )
    
    try:
        # Convert Pydantic models to Document objects
        from rag.core.types import Document
        
        documents = []
        for doc in payload.documents:
            # Create Document object with proper structure
            document = Document(
                id=doc.id,
                title=doc.title,
                source=doc.source,
                text=doc.text
            )
            documents.append(document)
            logger.debug(f"[INGEST] Processing document: {doc.title} (ID: {doc.id})")
        
        # Perform ingestion
        logger.info(f"[INGEST] Starting ingestion of {len(documents)} documents")
        result = await _ingester.ingest(documents)
        
        # Check result
        if result.isErr():
            error_msg = str(result.getError())
            logger.error(f"[INGEST] Ingestion failed: {error_msg}")
            raise HTTPException(
                status_code=400,
                detail=f"Ingestion failed: {error_msg}"
            )
        
        # Get chunk count from result
        chunk_count = result.getValue()
        logger.info(f"[INGEST] Successfully ingested {chunk_count} chunks from {len(documents)} documents")
        
        return IngestResponse(
            ingestedChunks=chunk_count,
            documentCount=len(documents),
            status="success",
            message=f"Successfully ingested {len(documents)} documents into {chunk_count} chunks"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[INGEST] Unexpected error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during ingestion: {str(e)}"
        )

@router.get("/ingest/status")
async def get_ingest_status() -> dict:
    """Get the status of the ingestion service"""
    return {
        "service": "ingest",
        "status": "ready" if _ingester is not None else "not_initialized",
        "ingester_type": type(_ingester).__name__ if _ingester else None
    }
