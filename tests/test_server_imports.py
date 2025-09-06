#!/usr/bin/env python
"""
Quick test to verify server can start without import errors
"""
import sys
import os

# Add rag module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rag'))

def test_imports():
    """Test all critical imports"""
    print("Testing imports...")
    
    try:
        from chunkers.utils import create_chunk_meta, generate_chunk_id, calculate_chunk_hash
        print("✅ chunkers.utils imports")
    except ImportError as e:
        print(f"❌ chunkers.utils: {e}")
        return False
    
    try:
        from chunkers.sentence_chunker import SentenceChunker
        print("✅ SentenceChunker")
    except ImportError as e:
        print(f"❌ SentenceChunker: {e}")
        return False
    
    try:
        from chunkers.paragraph_chunker import ParagraphChunker
        print("✅ ParagraphChunker")
    except ImportError as e:
        print(f"❌ ParagraphChunker: {e}")
        return False
    
    try:
        from chunkers.registry import registry
        print("✅ ChunkerRegistry")
    except ImportError as e:
        print(f"❌ ChunkerRegistry: {e}")
        return False
    
    try:
        from stores.chroma_store import ChromaVectorStore
        print("✅ ChromaVectorStore")
    except ImportError as e:
        print(f"❌ ChromaVectorStore: {e}")
        return False
    
    try:
        import server
        print("✅ server.py imports successfully")
    except ImportError as e:
        print(f"❌ server.py: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("="*60)
    print("Server Import Test")
    print("="*60)
    
    if test_imports():
        print("\n✅ All imports successful!")
        print("You can now start the server with:")
        print("  python start_server.py")
    else:
        print("\n❌ Import errors found. Please fix them before starting the server.")
