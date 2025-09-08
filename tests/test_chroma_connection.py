#!/usr/bin/env python
"""
Test ChromaDB connection and vector count
"""
import os
import sys
import chromadb
from pathlib import Path

def test_chroma_connection():
    """Test direct connection to ChromaDB"""
    print("=" * 60)
    print("Testing ChromaDB Connection")
    print("=" * 60)
    
    # Project root
    project_root = Path(__file__).parent
    print(f"Project root: {project_root}")
    
    # Test different path configurations
    paths_to_test = [
        "./chroma_db",
        "chroma_db",
        str(project_root / "chroma_db"),
        "E:\\Ragproject\\chroma_db"
    ]
    
    for path in paths_to_test:
        print(f"\nTesting path: {path}")
        
        # Resolve path
        if not os.path.isabs(path):
            resolved = project_root / path
        else:
            resolved = Path(path)
        
        print(f"  Resolved to: {resolved}")
        print(f"  Exists: {resolved.exists()}")
        
        if resolved.exists():
            try:
                # Try to connect
                client = chromadb.PersistentClient(path=str(resolved))
                
                # List collections
                collections = client.list_collections()
                print(f"  Collections found: {len(collections)}")
                
                for coll in collections:
                    try:
                        count = coll.count()
                        print(f"    - {coll.name}: {count} vectors")
                        
                        # Get metadata
                        metadata = coll.metadata if hasattr(coll, 'metadata') else {}
                        if metadata:
                            print(f"      Metadata: {metadata}")
                    except Exception as e:
                        print(f"    - {coll.name}: Error getting count: {e}")
                
                print(f"  ✅ Successfully connected to ChromaDB at {resolved}")
                return True
                
            except Exception as e:
                print(f"  ❌ Failed to connect: {e}")
    
    print("\n❌ Could not connect to ChromaDB at any path")
    return False

def test_api_endpoint():
    """Test the /api/rag/stats endpoint"""
    print("\n" + "=" * 60)
    print("Testing API Endpoint")
    print("=" * 60)
    
    try:
        import requests
        
        # Test endpoint
        response = requests.get("http://localhost:7001/api/rag/stats", timeout=5)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            print(f"  Total Vectors: {data.get('total_vectors', 0)}")
            print(f"  Store Type: {data.get('store_type', 'unknown')}")
            print(f"  Namespace: {data.get('namespace', 'unknown')}")
            print(f"  Status: {data.get('status', 'unknown')}")
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"Failed to test API: {e}")
        print("Is the server running on port 7001?")

if __name__ == "__main__":
    # Test direct connection
    success = test_chroma_connection()
    
    # Test API if server is running
    test_api_endpoint()
    
    sys.exit(0 if success else 1)
