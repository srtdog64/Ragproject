#!/usr/bin/env python
"""
Quick test script to verify the RAG system is working
"""

import sys
import time

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    try:
        import yaml
        print("✓ yaml")
    except ImportError:
        print("✗ yaml - Run: pip install pyyaml")
        return False
    
    try:
        import fastapi
        print("✓ fastapi")
    except ImportError:
        print("✗ fastapi - Run: pip install fastapi")
        return False
    
    try:
        import uvicorn
        print("✓ uvicorn")
    except ImportError:
        print("✗ uvicorn - Run: pip install uvicorn")
        return False
    
    try:
        from config_loader import config
        print("✓ config_loader")
    except ImportError as e:
        print(f"✗ config_loader - Error: {e}")
        return False
    
    try:
        sys.path.append('E:/Ragproject/rag')
        from chunkers.registry import registry
        print("✓ chunkers.registry")
    except ImportError as e:
        print(f"✗ chunkers.registry - Error: {e}")
        return False
    
    return True

def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")
    try:
        from config_loader import config
        
        # Test loading config
        policy_config = config.get_section('policy')
        print(f"✓ Policy config loaded: maxContextChars={policy_config.get('maxContextChars')}")
        
        chunker_config = config.get_section('chunker')
        print(f"✓ Chunker config loaded: default_strategy={chunker_config.get('default_strategy')}")
        
        return True
    except Exception as e:
        print(f"✗ Config loading failed: {e}")
        return False

def test_chunkers():
    """Test chunking strategies"""
    print("\nTesting chunking strategies...")
    try:
        sys.path.append('E:/Ragproject/rag')
        from chunkers.registry import registry
        from core.types import Document
        
        # List strategies
        strategies = registry.list_strategies()
        print(f"✓ Found {len(strategies)} strategies:")
        for s in strategies:
            print(f"  - {s['name']}: {s['description']}")
        
        # Test chunking
        test_doc = Document(
            id="test1",
            title="Test Document",
            source="test",
            text="This is a test document. It has multiple sentences. Each sentence is separated by a period."
        )
        
        chunker = registry.get_chunker("sentence")
        params = registry.get_params()
        chunks = chunker.chunk(test_doc, params)
        print(f"✓ Sentence chunker produced {len(chunks)} chunks")
        
        return True
    except Exception as e:
        print(f"✗ Chunker test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_server_startup():
    """Test if server can start"""
    print("\nTesting server startup...")
    try:
        from server import app, buildContainer, buildPipeline
        
        # Test container building
        container = buildContainer()
        print("✓ DI container built successfully")
        
        # Test pipeline building
        ingester, pipeline = buildPipeline(container)
        print("✓ Pipeline built successfully")
        
        print("✓ Server can be started")
        return True
    except Exception as e:
        print(f"✗ Server startup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 50)
    print("RAG System Health Check")
    print("=" * 50)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("Chunkers", test_chunkers()))
    results.append(("Server", test_server_startup()))
    
    # Summary
    print("\n" + "=" * 50)
    print("Summary:")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:20} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 50)
    
    if all_passed:
        print("\n✅ All tests passed! System is ready.")
        print("\nTo start the server, run:")
        print("  python server.py")
        print("\nTo test chunking strategies, run:")
        print("  python test_chunking.py")
    else:
        print("\n⚠️ Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  1. Install missing packages: pip install -r requirements.txt")
        print("  2. Make sure config.yaml exists in the project root")
        print("  3. Check that all file paths are correct")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
