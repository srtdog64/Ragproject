# chunkers/api_router.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sys
sys.path.append('E:/Ragproject/rag')
from chunkers.registry import registry
from chunkers.base import ChunkingParams
from core.types import Document

router = APIRouter(prefix="/api/chunkers", tags=["chunkers"])

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

@router.get("/strategies")
async def list_strategies():
    """List all available chunking strategies"""
    strategies = registry.list_strategies()
    return {
        "strategies": strategies,
        "current": registry.get_current_strategy()
    }

@router.get("/strategy")
async def get_current_strategy():
    """Get current chunking strategy"""
    return {
        "strategy": registry.get_current_strategy(),
        "params": registry.get_params().__dict__
    }

@router.get("/current")
async def get_current():
    """Get current chunking strategy (alias for compatibility)"""
    return {
        "strategy": registry.get_current_strategy(),
        "params": registry.get_params().__dict__
    }

@router.post("/strategy")
async def set_strategy(request: StrategyRequest):
    """Set chunking strategy"""
    try:
        registry.set_strategy(request.strategy)
        return {
            "message": f"Strategy set to {request.strategy}",
            "strategy": registry.get_current_strategy()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/params")
async def get_params():
    """Get current chunking parameters"""
    # Use get_params_dict for faster access
    return registry.get_params_dict()

@router.post("/params")
async def set_params(request: ParamsRequest):
    """Update chunking parameters"""
    try:
        # Only update non-None values
        params_dict = {k: v for k, v in request.dict().items() if v is not None}
        registry.set_params(**params_dict)
        return {
            "message": "Parameters updated",
            "params": registry.get_params().__dict__
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/analyze")
async def analyze_text(request: AnalyzeRequest):
    """Analyze text and suggest best chunking strategy"""
    suggested = registry.analyze_text(request.text)
    return {
        "suggested_strategy": suggested,
        "text_length": len(request.text)
    }

@router.post("/preview")
async def preview_chunking(request: PreviewRequest):
    """Preview chunking with specific strategy"""
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
        
        # Convert chunks to JSON-serializable format
        chunks_data = [
            {
                "id": chunk.id,
                "text": chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text,
                "length": len(chunk.text),
                "meta": chunk.meta
            }
            for chunk in chunks
        ]
        
        return {
            "strategy": strategy,
            "chunks": chunks_data,
            "total_chunks": len(chunks),
            "params": params.__dict__
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
