#!/usr/bin/env python
"""
Test API endpoint availability
"""
import requests
import json

def test_endpoints():
    """Test various API endpoints"""
    base_url = "http://localhost:7001"
    
    print("Testing API endpoints...")
    print("=" * 60)
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=2)
        print(f"✓ /health: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"✗ /health: {e}")
    
    # Test docs endpoint
    try:
        response = requests.get(f"{base_url}/docs", timeout=2)
        print(f"✓ /docs: {response.status_code}")
    except Exception as e:
        print(f"✗ /docs: {e}")
    
    # Test rag stats endpoint
    try:
        response = requests.get(f"{base_url}/api/rag/stats", timeout=2)
        print(f"✓ /api/rag/stats: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"  Response: {response.text}")
    except Exception as e:
        print(f"✗ /api/rag/stats: {e}")
    
    # List all available routes (if possible)
    print("\n" + "=" * 60)
    print("Available routes from server:")
    try:
        # FastAPI exposes openapi.json
        response = requests.get(f"{base_url}/openapi.json", timeout=2)
        if response.status_code == 200:
            api_spec = response.json()
            paths = api_spec.get("paths", {})
            for path in sorted(paths.keys()):
                methods = list(paths[path].keys())
                print(f"  {path}: {', '.join(methods).upper()}")
    except Exception as e:
        print(f"  Could not retrieve routes: {e}")

if __name__ == "__main__":
    test_endpoints()
