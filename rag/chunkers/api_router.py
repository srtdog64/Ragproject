# chunkers/api_router.py
"""
Chunking API Router
Provides RESTful endpoints for chunking strategy management
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from .registry import registry
from rag.chunkers.base import ChunkingParams
from rag.core.types import Document

router = APIRouter(prefix="/api/chunkers", tags=["chunkers"])

# === Request Models ===
class StrategyRequest(BaseModel):
    strategy: str

class ParamsRequest(BaseModel):
    maxTokens: Optional[int] = None
    windowSize: Optional[int] = None
    overlap: Optional[int] = None
    semanticThreshold: Optional[float] = None
    language: Optional[str] = None
    sentenceMinLen: Optional[int] = None
    paragraphMinLen: Optional[int] = None

class AnalyzeRequest(BaseModel):
    text: str

class PreviewRequest(BaseModel):
    text: str
    strategy: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    title: Optional[str] = "Preview Document"
    source: Optional[str] = "preview"

# === Strategy Management Endpoints ===
@router.get("/strategies")
async def list_strategies():
    """List all available chunking strategies with current selection"""
    strategies = registry.list_strategies()
    return {
        "strategies": strategies,
        "current": registry.get_current_strategy()
    }

@router.get("/strategy")
async def get_current_strategy():
    """Get the currently active chunking strategy and its parameters"""
    return {
        "strategy": registry.get_current_strategy(),
        "params": registry.get_params_dict()
    }

@router.post("/strategy")
async def set_strategy(request: StrategyRequest):
    """Set the active chunking strategy"""
    try:
        registry.set_strategy(request.strategy)
        return {
            "message": f"Strategy set to {request.strategy}",
            "strategy": registry.get_current_strategy(),
            "params": registry.get_params_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# === Parameters Management Endpoints ===
@router.get("/params")
async def get_params():
    """Get current chunking parameters"""
    return registry.get_params_dict()

@router.post("/params")
async def set_params(request: ParamsRequest):
    """Update chunking parameters (partial update supported)"""
    try:
        # Only update non-None values
        params_dict = {k: v for k, v in request.dict().items() if v is not None}
        if params_dict:
            registry.set_params(**params_dict)
        return {
            "message": "Parameters updated successfully",
            "params": registry.get_params_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# === Analysis and Preview Endpoints ===
@router.post("/analyze")
async def analyze_text(request: AnalyzeRequest):
    """Analyze text characteristics and suggest optimal chunking strategy"""
    suggested = registry.analyze_text(request.text)
    
    # Get text statistics
    lines = request.text.split('\n')
    words = request.text.split()
    
    return {
        "suggested_strategy": suggested,
        "text_stats": {
            "length": len(request.text),
            "lines": len(lines),
            "words": len(words),
            "avg_line_length": len(request.text) / max(1, len(lines))
        }
    }

@router.post("/preview")
async def preview_chunking(request: PreviewRequest):
    """
    Preview how text would be chunked with specified strategy and parameters.
    Useful for testing different strategies before applying them.
    """
    strategy = request.strategy or registry.get_current_strategy()
    
    try:
        chunker = registry.get_chunker(strategy)
        params = registry.get_params()
        
        # Override params if provided
        if request.params:
            params_dict = params.__dict__.copy()
            params_dict.update(request.params)
            params = ChunkingParams(**params_dict)
        
        # Create temporary document
        doc = Document(
            id="preview",
            title=request.title,
            source=request.source,
            text=request.text
        )
        
        # Perform chunking
        chunks = chunker.chunk(doc, params)
        
        # Convert chunks to JSON-serializable format with preview
        chunks_data = []
        for i, chunk in enumerate(chunks):
            preview_length = 200
            chunk_data = {
                "id": chunk.id,
                "index": i,
                "text_preview": chunk.text[:preview_length] + "..." if len(chunk.text) > preview_length else chunk.text,
                "length": len(chunk.text),
                "meta": chunk.meta
            }
            chunks_data.append(chunk_data)
        
        return {
            "strategy": strategy,
            "chunks": chunks_data,
            "summary": {
                "total_chunks": len(chunks),
                "avg_chunk_size": sum(len(c.text) for c in chunks) / max(1, len(chunks)),
                "min_chunk_size": min(len(c.text) for c in chunks) if chunks else 0,
                "max_chunk_size": max(len(c.text) for c in chunks) if chunks else 0
            },
            "params": params.__dict__
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === Health Check ===
@router.get("/health")
async def health_check():
    """Check if chunking service is operational"""
    try:
        strategy = registry.get_current_strategy()
        chunker = registry.get_chunker(strategy)
        return {
            "status": "healthy",
            "current_strategy": strategy,
            "available_strategies": len(registry._chunkers)
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")
