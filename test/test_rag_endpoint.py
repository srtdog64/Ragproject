#!/usr/bin/env python
"""
Test /api/rag/stats endpoint directly
"""
import requests
import json

def test_rag_stats():
    """Test the /api/rag/stats endpoint"""
    print("="*60)
    print("Testing /api/rag/stats Endpoint")
    print("="*60)
    
    base_url = "http://localhost:7001"
    
    # Test health first
    print("\n1. Testing /health:")
    try:
        response = requests.get(f"{base_url}/health", timeout=2)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test /api/rag/stats with detailed info
    print("\n2. Testing /api/rag/stats:")
    try:
        response = requests.get(f"{base_url}/api/rag/stats", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   URL: {response.url}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Success! Response:")
            print(f"     - Total vectors: {data.get('total_vectors', 0)}")
            print(f"     - Namespace: {data.get('namespace', 'unknown')}")
            print(f"     - Store type: {data.get('store_type', 'unknown')}")
            print(f"     - Status: {data.get('status', 'unknown')}")
        else:
            print(f"   Failed! Response: {response.text}")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # Check what routes are actually registered
    print("\n3. Checking registered routes:")
    try:
        response = requests.get(f"{base_url}/openapi.json", timeout=2)
        if response.status_code == 200:
            spec = response.json()
            paths = spec.get("paths", {})
            
            if "/api/rag/stats" in paths:
                print("   /api/rag/stats IS registered!")
                print(f"   Methods: {list(paths['/api/rag/stats'].keys())}")
            else:
                print("   /api/rag/stats NOT found in OpenAPI spec")
                
            # Show all /api/rag/* routes
            rag_routes = [p for p in paths if p.startswith("/api/rag/")]
            if rag_routes:
                print(f"\n   Found RAG routes:")
                for route in rag_routes:
                    print(f"     - {route}")
            else:
                print("   No /api/rag/* routes found!")
                
    except Exception as e:
        print(f"   Error checking routes: {e}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    test_rag_stats()
