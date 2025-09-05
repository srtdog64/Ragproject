#!/usr/bin/env python
"""
Debug script for checking RAG system state
"""
import requests
import json
import sys
import os

# Add rag module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rag'))

def check_server():
    """Check if server is running"""
    try:
        response = requests.get("http://localhost:7001/health")
        if response.status_code == 200:
            print("✅ Server is running")
            print(f"   Response: {response.json()}")
            return True
        else:
            print("❌ Server returned error")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running")
        return False

def check_chunker_api():
    """Check chunker API"""
    try:
        # Get current strategy
        response = requests.get("http://localhost:7001/api/chunkers/strategy")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Current chunking strategy: {data.get('strategy', 'unknown')}")
        else:
            print("❌ Failed to get chunking strategy")
            
        # List strategies
        response = requests.get("http://localhost:7001/api/chunkers/strategies")
        if response.status_code == 200:
            strategies = response.json()
            print(f"✅ Available strategies: {len(strategies)} found")
            for s in strategies:
                active = " (ACTIVE)" if s.get('active') else ""
                print(f"   - {s['name']}{active}: {s['description'][:50]}...")
        else:
            print("❌ Failed to list strategies")
            
    except Exception as e:
        print(f"❌ Chunker API error: {e}")

def ingest_sample_data():
    """Ingest sample data for testing"""
    sample_docs = [
        {
            "id": "test-001",
            "title": "RAG System Overview",
            "source": "test",
            "text": """
            Retrieval-Augmented Generation (RAG) is a technique that enhances 
            large language models by retrieving relevant information from a 
            knowledge base before generating responses. This approach combines 
            the power of retrieval systems with generative AI models.
            
            RAG systems typically consist of three main components:
            1. Document ingestion and chunking
            2. Vector embedding and storage
            3. Retrieval and generation pipeline
            
            The chunking strategy is crucial for RAG performance. Different 
            strategies like sentence-based, paragraph-based, or sliding window 
            chunking can be used depending on the document type.
            """
        },
        {
            "id": "test-002",
            "title": "Embeddings in RAG",
            "source": "test",
            "text": """
            Embeddings are numerical representations of text that capture 
            semantic meaning. In RAG systems, embeddings are used to find 
            similar content in the knowledge base.
            
            Modern embedding models like Sentence-BERT can encode text into 
            dense vectors. These vectors can then be stored in vector databases 
            for efficient similarity search.
            
            한국어 텍스트도 임베딩할 수 있습니다. 다국어 모델을 사용하면 
            여러 언어의 텍스트를 동일한 벡터 공간에 매핑할 수 있습니다.
            """
        }
    ]
    
    try:
        response = requests.post(
            "http://localhost:7001/ingest",
            json={"documents": sample_docs},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sample data ingested successfully")
            print(f"   Chunks created: {data.get('ingestedChunks', 0)}")
            print(f"   Documents: {data.get('documentCount', 0)}")
            return True
        else:
            print(f"❌ Failed to ingest data: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ingestion error: {e}")
        return False

def test_ask_endpoint():
    """Test the /ask endpoint"""
    test_questions = [
        "What is RAG?",
        "How do embeddings work?",
        "한국어 텍스트 처리는 어떻게 하나요?",
        "What are the main components of RAG?"
    ]
    
    for question in test_questions:
        print(f"\n📝 Testing question: {question}")
        try:
            response = requests.post(
                "http://localhost:7001/ask",
                json={"question": question},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success!")
                print(f"   Answer: {data['answer'][:100]}...")
                print(f"   Request ID: {data['requestId']}")
                print(f"   Latency: {data['latencyMs']}ms")
                print(f"   Context IDs: {data.get('ctxIds', [])}")
            else:
                print(f"❌ Failed with status {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")

def main():
    print("=" * 60)
    print("RAG System Debug Tool")
    print("=" * 60)
    
    # 1. Check server health
    print("\n1. Checking server health...")
    if not check_server():
        print("Please start the server first: python start_server.py")
        return
    
    # 2. Check chunker API
    print("\n2. Checking chunker configuration...")
    check_chunker_api()
    
    # 3. Ingest sample data
    print("\n3. Ingesting sample data...")
    if not ingest_sample_data():
        print("Failed to ingest data, but continuing tests...")
    
    # 4. Test ask endpoint
    print("\n4. Testing /ask endpoint...")
    test_ask_endpoint()
    
    print("\n" + "=" * 60)
    print("Debug completed!")

if __name__ == "__main__":
    main()
