# tests/__init__.py
"""
Test suite for RAG system
"""

# Test categories
__all__ = [
    # Unit tests
    'test_chunking',
    'test_chunker_api',
    'test_wrapper',
    'test_embedder_manager',
    
    # Integration tests
    'test_client',
    'test_gemini',
    
    # System checks
    'check_system',
    'health_check',
    'debug_chunker',
]
