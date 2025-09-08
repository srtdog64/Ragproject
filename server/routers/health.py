"""
Health Check Router
"""
from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check() -> dict:
    """Basic health check endpoint"""
    return {
        "status": "ok",
        "service": "RAG",
        "llm": "Gemini"
    }

@router.get("/api/health/detailed")
async def detailed_health() -> dict:
    """Detailed health check with component status"""
    # This will be enhanced to check actual component health
    return {
        "status": "ok",
        "components": {
            "llm": "ok",
            "vector_store": "ok",
            "embedder": "ok",
            "chunker": "ok"
        }
    }
