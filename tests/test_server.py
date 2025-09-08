#!/usr/bin/env python
"""
Final comprehensive test for RAG server
Consolidates all test functionality
"""
import requests
import time
import sys

def test_server():
    """Test all server endpoints"""
    base_url = "http://localhost:7001"
    results = []
    
    print("="*60)
    print("RAG Server Comprehensive Test")
    print("="*60)
    
    # 1. Health check
    print("\n1. Health Check...")
    try:
        r = requests.get(f"{base_url}/health", timeout=3)
        if r.status_code == 200:
            print(f"   ✓ Health: {r.json()['status']}")
            results.append(("Health", True))
        else:
            print(f"   ✗ Health failed: {r.status_code}")
            results.append(("Health", False))
    except Exception as e:
        print(f"   ✗ Health error: {e}")
        results.append(("Health", False))
    
    # 2. RAG Stats - THE MAIN TEST
    print("\n2. Vector Stats API...")
    try:
        r = requests.get(f"{base_url}/api/rag/stats", timeout=5)
        if r.status_code == 200:
            data = r.json()
            count = data.get('total_vectors', 0)
            print(f"   ✓ Vector Count: {count:,}")
            print(f"   ✓ Namespace: {data.get('namespace')}")
            print(f"   ✓ Store Type: {data.get('store_type')}")
            results.append(("Vector Stats", True))
        else:
            print(f"   ✗ Vector Stats failed: {r.status_code}")
            results.append(("Vector Stats", False))
    except Exception as e:
        print(f"   ✗ Vector Stats error: {e}")
        results.append(("Vector Stats", False))
    
    # 3. Collections
    print("\n3. Collections API...")
    try:
        r = requests.get(f"{base_url}/api/rag/collections", timeout=5)
        if r.status_code == 200:
            data = r.json()
            collections = data.get('collections', [])
            print(f"   ✓ Found {len(collections)} collections")
            for coll in collections[:3]:  # Show first 3
                print(f"     - {coll.get('name')}: {coll.get('count', 0)} vectors")
            results.append(("Collections", True))
        else:
            print(f"   ✗ Collections failed: {r.status_code}")
            results.append(("Collections", False))
    except Exception as e:
        print(f"   ✗ Collections error: {e}")
        results.append(("Collections", False))
    
    # 4. Chunker strategies
    print("\n4. Chunker Strategies...")
    try:
        r = requests.get(f"{base_url}/api/chunkers/strategies", timeout=3)
        if r.status_code == 200:
            strategies = r.json()
            print(f"   ✓ Available strategies: {len(strategies)}")
            results.append(("Chunker", True))
        else:
            print(f"   ✗ Chunker failed: {r.status_code}")
            results.append(("Chunker", False))
    except Exception as e:
        print(f"   ✗ Chunker error: {e}")
        results.append(("Chunker", False))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary:")
    passed = sum(1 for _, status in results if status)
    total = len(results)
    
    for name, status in results:
        status_str = "✓ PASS" if status else "✗ FAIL"
        print(f"  {name:20} {status_str}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓✓✓ ALL TESTS PASSED! Server is fully operational.")
    else:
        print(f"\n⚠ {total - passed} tests failed. Check server logs.")
    
    print("="*60)
    
    return passed == total

if __name__ == "__main__":
    success = test_server()
    sys.exit(0 if success else 1)
