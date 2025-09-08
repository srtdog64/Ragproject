#!/usr/bin/env python
"""Test the RAG API endpoints directly"""
import requests

def test_endpoints():
    base_url = "http://localhost:7001"
    
    # Test health endpoint
    print("Testing /health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Test /api/rag/stats endpoint
    print("\nTesting /api/rag/stats endpoint...")
    try:
        response = requests.get(f"{base_url}/api/rag/stats", timeout=5)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
        else:
            print(f"  Response: {response.text}")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Test /api/rag/collections endpoint
    print("\nTesting /api/rag/collections endpoint...")
    try:
        response = requests.get(f"{base_url}/api/rag/collections", timeout=5)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
        else:
            print(f"  Response: {response.text}")
    except Exception as e:
        print(f"  Error: {e}")

if __name__ == "__main__":
    test_endpoints()
