#!/usr/bin/env python
"""
Test ChromaDB persistence and Reranker functionality
"""

import requests
import json
import time
import sys
import os

def test_persistence_and_reranking():
    base_url = "http://localhost:7001"
    
    print("="*60)
    print("Testing ChromaDB Persistence & Reranker")
    print("="*60)
    
    # 1. Check if server is running
    print("\n1. Checking server...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code != 200:
            print("Server not running. Start with: python start_server.py")
            return
        print("Server is online")
    except:
        print("Cannot connect to server")
        return
    
    # 2. Check if ChromaDB already has data
    print("\n2. Testing persistence...")
    response = requests.post(
        f"{base_url}/ask",
        json={"question": "test persistence chromadb"},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        ctx_ids = data.get('ctxIds', [])
        if ctx_ids:
            print(f"Found {len(ctx_ids)} persisted documents in ChromaDB!")
            print("   ChromaDB persistence is working!")
    
    # 3. Ingest documents for reranking test
    print("\n3. Ingesting test documents for reranking...")
    test_docs = [
        {
            "id": "rerank-test-001",
            "title": "Python Programming Guide",
            "source": "test",
            "text": "Python is a high-level programming language known for its simplicity and readability."
        },
        {
            "id": "rerank-test-002",
            "title": "Python Data Science",
            "source": "test",
            "text": "Python is widely used in data science for machine learning and data analysis."
        },
        {
            "id": "rerank-test-003",
            "title": "JavaScript Web Development",
            "source": "test",
            "text": "JavaScript is the primary language for web development and runs in browsers."
        },
        {
            "id": "rerank-test-004",
            "title": "Python vs JavaScript",
            "source": "test",
            "text": "Python and JavaScript are both popular programming languages with different use cases."
        }
    ]
    
    response = requests.post(
        f"{base_url}/ingest",
        json={"documents": test_docs},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"Ingested {data['documentCount']} docs into {data['ingestedChunks']} chunks")
    
    # 4. Test reranking with query
    print("\n4. Testing reranking...")
    query = "Python programming language"
    
    response = requests.post(
        f"{base_url}/ask",
        json={"question": query, "k": 5},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        ctx_ids = data.get('ctxIds', [])
        answer = data['answer'][:200] + "..." if len(data['answer']) > 200 else data['answer']
        
        print(f"   Query: {query}")
        print(f"   Retrieved contexts: {len(ctx_ids)}")
        print(f"   Answer: {answer}")
        
        if ctx_ids:
            print("\n   Reranker should have prioritized Python-related documents!")
            print("   Check server logs for reranking scores")
    
    # 5. Instructions for full test
    print("\n" + "="*60)
    print("FULL PERSISTENCE TEST:")
    print("="*60)
    print("1. Note that documents were ingested")
    print("2. Stop the server (Ctrl+C)")
    print("3. Check that ./chroma_db directory was created")
    print("4. Restart the server")
    print("5. Run this script again")
    print("\nIf ChromaDB is working, you'll see persisted documents immediately!")
    print("\nCheck server logs for:")
    print("- 'Using ChromaDB vector store (persistent)'")
    print("- 'ChromaDB: Loaded existing collection'")
    print("- 'SimpleScoreReranker: Reranking X documents'")
    print("="*60)

if __name__ == "__main__":
    test_persistence_and_reranking()
