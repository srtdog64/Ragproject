#!/usr/bin/env python
"""
Check vector store persistence and functionality
"""

import requests
import json
import time
import sys

def check_vector_store():
    base_url = "http://localhost:7001"
    
    print("="*60)
    print("Vector Store Persistence Check")
    print("="*60)
    
    # 1. Check current store status
    print("\n1. Checking server health...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code != 200:
            print("Server not running. Start with: python start_server.py")
            return
        print("Server is running")
    except:
        print("Cannot connect to server")
        return
    
    # 2. Ingest test document
    print("\n2. Ingesting test document...")
    test_doc = {
        "id": "persistence-test-001",
        "title": "Persistence Test",
        "source": "test",
        "text": "This is a test document for checking vector store persistence. If you can retrieve this after server restart, persistence is working."
    }
    
    response = requests.post(
        f"{base_url}/ingest",
        json={"documents": [test_doc]},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"Ingested: {data['ingestedChunks']} chunks")
    else:
        print(f"Ingestion failed: {response.status_code}")
        return
    
    # 3. Test immediate retrieval
    print("\n3. Testing immediate retrieval...")
    response = requests.post(
        f"{base_url}/ask",
        json={"question": "persistence test document"},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        ctx_ids = data.get('ctxIds', [])
        if ctx_ids:
            print(f"Retrieved {len(ctx_ids)} contexts immediately")
        else:
            print("No contexts retrieved immediately (PROBLEM!)")
    
    # 4. Instructions for persistence test
    print("\n" + "="*60)
    print("PERSISTENCE TEST INSTRUCTIONS:")
    print("="*60)
    print("1. Note that we ingested a test document")
    print("2. Now RESTART the server (Ctrl+C and restart)")
    print("3. Run this script again with --check flag:")
    print("   python check_vector_store.py --check")
    print("\nIf InMemoryVectorStore is used (current), data will be LOST")
    print("If persistent store is used, data will be RETAINED")
    print("="*60)

def check_after_restart():
    base_url = "http://localhost:7001"
    
    print("="*60)
    print("Checking After Server Restart")
    print("="*60)
    
    # Check if test document is still there
    print("\n1. Checking if test document persisted...")
    response = requests.post(
        f"{base_url}/ask",
        json={"question": "persistence test document"},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        ctx_ids = data.get('ctxIds', [])
        if ctx_ids:
            print("PERSISTENCE WORKING! Retrieved contexts after restart")
            print("   This means a persistent store is being used")
        else:
            print("NO PERSISTENCE! Data was lost after restart")
            print("   This confirms InMemoryVectorStore is being used")
            print("\nTo fix this, we need to implement:")
            print("1. ChromaDB integration (already in requirements.txt)")
            print("2. FAISS integration (already in requirements.txt)")
            print("3. Or another persistent vector store")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        check_after_restart()
    else:
        check_vector_store()
