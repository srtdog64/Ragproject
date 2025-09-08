#!/usr/bin/env python
"""
Debug RAG router registration
"""
import requests
import json

def debug_routes():
    """Check what routes are actually available"""
    base_url = "http://localhost:7001"
    
    print("="*60)
    print("RAG Router Debug")
    print("="*60)
    
    # Try to get OpenAPI spec
    print("\n1. Getting OpenAPI spec...")
    try:
        r = requests.get(f"{base_url}/openapi.json", timeout=3)
        if r.status_code == 200:
            spec = r.json()
            paths = spec.get('paths', {})
            print(f"   ✓ Found {len(paths)} paths:")
            for path in sorted(paths.keys()):
                methods = list(paths[path].keys())
                print(f"     {path}: {', '.join(methods).upper()}")
        else:
            print(f"   ✗ OpenAPI failed: {r.status_code}")
    except Exception as e:
        print(f"   ✗ OpenAPI error: {e}")
    
    # Test specific endpoints
    print("\n2. Testing RAG endpoints directly...")
    
    endpoints = [
        ("/health", "GET"),
        ("/api/rag/stats", "GET"),
        ("/api/rag/collections", "GET"),
        ("/api/chunkers/strategies", "GET"),
        ("/api/health/detailed", "GET"),
    ]
    
    for path, method in endpoints:
        print(f"\n   Testing {method} {path}...")
        try:
            if method == "GET":
                r = requests.get(f"{base_url}{path}", timeout=3)
            else:
                r = requests.request(method, f"{base_url}{path}", timeout=3)
            
            print(f"     Status: {r.status_code}")
            if r.status_code == 200:
                print(f"     ✓ Success")
                # Show first 100 chars of response
                text = r.text[:100] + "..." if len(r.text) > 100 else r.text
                print(f"     Response: {text}")
            else:
                print(f"     ✗ Failed")
                print(f"     Response: {r.text[:200]}")
        except Exception as e:
            print(f"     ✗ Error: {e}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    debug_routes()
