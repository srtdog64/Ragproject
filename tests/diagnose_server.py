#!/usr/bin/env python
"""
Test server startup and diagnose any issues
"""

import sys
import os

# Add rag module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rag'))

def test_imports():
    """Test if all required modules can be imported"""
    
    print("Testing imports...")
    errors = []
    
    # Test core imports
    try:
        import uvicorn
        print("✅ uvicorn")
    except ImportError as e:
        errors.append(f"❌ uvicorn: {e}")
        
    try:
        import chromadb
        print("✅ chromadb")
    except ImportError as e:
        errors.append(f"❌ chromadb: {e}")
        print("   Install with: pip install chromadb")
    
    try:
        import sentence_transformers
        print("✅ sentence_transformers")
    except ImportError as e:
        errors.append(f"❌ sentence_transformers: {e}")
        print("   Install with: pip install sentence-transformers")
    
    # Test our modules
    try:
        from stores.chroma_store import ChromaVectorStore
        print("✅ ChromaVectorStore")
    except ImportError as e:
        errors.append(f"❌ ChromaVectorStore: {e}")
    
    try:
        from rerankers.factory import RerankerFactory
        print("✅ RerankerFactory")
    except ImportError as e:
        errors.append(f"❌ RerankerFactory: {e}")
    
    try:
        from rerankers.cross_encoder_reranker import SimpleScoreReranker
        print("✅ SimpleScoreReranker")
    except ImportError as e:
        errors.append(f"❌ SimpleScoreReranker: {e}")
    
    return errors

def test_server_import():
    """Test if server.py can be imported"""
    print("\nTesting server.py import...")
    try:
        import server
        print("✅ server.py imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import server.py: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("="*60)
    print("RAG Server Startup Diagnostics")
    print("="*60)
    
    # Test imports
    errors = test_imports()
    
    if errors:
        print("\n" + "="*60)
        print("IMPORT ERRORS FOUND:")
        print("="*60)
        for error in errors:
            print(error)
        print("\nPlease install missing dependencies:")
        print("pip install -r requirements.txt")
        print("\nOr specifically:")
        print("pip install chromadb sentence-transformers")
        return
    
    # Test server import
    if test_server_import():
        print("\n" + "="*60)
        print("ALL TESTS PASSED!")
        print("="*60)
        print("\nYou can now start the server with:")
        print("  python start_server.py")
        print("\nOr run the check script:")
        print("  python check_server.py")
    else:
        print("\nPlease fix the import errors above before starting the server")

if __name__ == "__main__":
    main()
