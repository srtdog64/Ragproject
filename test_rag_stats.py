#!/usr/bin/env python
"""
Debug script to test /api/rag/stats endpoint
"""
import requests
import json

def test_endpoints():
    """Test API endpoints with detailed output"""
    base_url = "http://localhost:7001"
    
    print("=" * 60)
    print("Testing RAG API Endpoints")
    print("=" * 60)
    
    # Test health first
    print("\n1. Testing /health endpoint:")
    try:
        response = requests.get(f"{base_url}/health", timeout=2)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test /api/rag/stats
    print("\n2. Testing /api/rag/stats endpoint:")
    try:
        response = requests.get(f"{base_url}/api/rag/stats", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print(f"   Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"   Response Text: {response.text}")
            
            # Try to parse error
            try:
                error_data = response.json()
                print(f"   Error Detail: {error_data.get('detail', 'No detail')}")
            except:
                pass
                
    except Exception as e:
        print(f"   Error: {e}")
    
    # List all available routes
    print("\n3. Available API routes:")
    try:
        response = requests.get(f"{base_url}/openapi.json", timeout=2)
        if response.status_code == 200:
            api_spec = response.json()
            paths = api_spec.get("paths", {})
            
            # Group by prefix
            api_routes = [p for p in paths.keys() if p.startswith("/api/")]
            other_routes = [p for p in paths.keys() if not p.startswith("/api/")]
            
            print("\n   API Routes:")
            for path in sorted(api_routes):
                methods = list(paths[path].keys())
                print(f"      {path}: {', '.join(methods).upper()}")
            
            print("\n   Other Routes:")
            for path in sorted(other_routes):
                methods = list(paths[path].keys())
                print(f"      {path}: {', '.join(methods).upper()}")
                
    except Exception as e:
        print(f"   Could not retrieve routes: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_endpoints()
