#!/usr/bin/env python
"""
Debug script for chunker registry
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rag'))

print("Testing Chunker Registry...")
print("=" * 60)

try:
    # Test direct import
    print("1. Testing direct import of registry...")
    from chunkers.registry import registry
    print(f"   Registry initialized: {registry._initialized}")
    print(f"   Current strategy: {registry.get_current_strategy()}")
    print()
    
    # Test list strategies
    print("2. Testing list_strategies()...")
    strategies = registry.list_strategies()
    print(f"   Found {len(strategies)} strategies:")
    for s in strategies:
        active = " (ACTIVE)" if s['active'] else ""
        print(f"   - {s['name']}: {s['description'][:50]}...{active}")
    print()
    
    # Test get params
    print("3. Testing get_params_dict()...")
    params = registry.get_params_dict()
    print(f"   Parameters: {params}")
    print()
    
    # Test API
    print("4. Testing via API...")
    import requests
    base_url = "http://localhost:7001"
    
    response = requests.get(f"{base_url}/api/chunkers/strategies", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"   API Response OK: {len(data.get('strategies', []))} strategies")
        print(f"   Current strategy from API: {data.get('current')}")
    else:
        print(f"   API Error: {response.status_code} - {response.text}")
    
    print("\n" + "=" * 60)
    print("Test completed successfully!")
    
except Exception as e:
    import traceback
    print(f"\nERROR: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
