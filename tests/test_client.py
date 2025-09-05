#!/usr/bin/env python
"""
RAG Service Test Client
Tests basic operations of the RAG service
"""

import requests
import json
import time

BASE_URL = "http://localhost:7001"

def testHealth():
    print("Testing /health endpoint...")
    res = requests.get(f"{BASE_URL}/health")
    print(f"Status: {res.status_code}")
    print(f"Response: {res.json()}\n")

def testIngest():
    print("Testing /ingest endpoint...")
    # Load sample documents
    with open("sample_docs.json", "r") as f:
        payload = json.load(f)
    
    res = requests.post(f"{BASE_URL}/ingest", json=payload)
    print(f"Status: {res.status_code}")
    print(f"Response: {res.json()}\n")
    return res.status_code == 200

def testAsk(question: str, k: int = None):
    print(f"Testing /ask endpoint with question: '{question}'")
    payload = {"question": question}
    if k is not None:
        payload["k"] = k
    
    res = requests.post(f"{BASE_URL}/ask", json=payload)
    print(f"Status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        print(f"Answer: {data['answer']}")
        print(f"Context IDs: {data['ctxIds']}")
        print(f"Request ID: {data['requestId']}")
        print(f"Latency: {data['latencyMs']}ms\n")
    else:
        print(f"Error: {res.text}\n")

def main():
    print("=" * 60)
    print("RAG Service Test Client")
    print("=" * 60 + "\n")
    
    # Test health
    testHealth()
    
    # Test ingestion
    print("Ingesting sample documents...")
    if testIngest():
        time.sleep(1)  # Give system time to process
        
        # Test various questions
        questions = [
            "What is RAG?",
            "How do vector databases work in RAG systems?",
            "What are chunking strategies?",
            "Explain reranking",
            "What are LLM integration patterns?"
        ]
        
        for q in questions:
            testAsk(q, k=3)
            time.sleep(0.5)  # Avoid overwhelming the service
    
    print("Test completed!")

if __name__ == "__main__":
    main()
