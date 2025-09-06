#!/usr/bin/env python
"""
Diagnose why RAG system can't retrieve indexed documents
"""

import requests
import json
import time

def test_full_cycle():
    """Test complete RAG cycle: ingest -> retrieve"""
    base_url = "http://localhost:7001"
    
    print("="*60)
    print("RAG System Diagnostic")
    print("="*60)
    
    # 1. Check server health
    print("\n1. Checking server health...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Server is healthy")
        else:
            print("❌ Server health check failed")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    # 2. Check current strategy
    print("\n2. Checking chunking strategy...")
    response = requests.get(f"{base_url}/api/chunkers/strategy")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Strategy: {data['strategy']}")
        print(f"   Params: {json.dumps(data['params'], indent=2)}")
    
    # 3. Ingest test documents
    print("\n3. Ingesting test documents...")
    test_docs = [
        {
            "id": "test-001",
            "title": "RAG 시스템 테스트",
            "source": "diagnostic",
            "text": """
            RAG(Retrieval-Augmented Generation) 시스템은 문서를 검색하고 
            생성하는 강력한 AI 시스템입니다. 이 시스템은 다음과 같은 
            주요 구성요소를 가지고 있습니다:
            
            1. 문서 청킹 (Document Chunking)
            텍스트를 적절한 크기로 분할합니다.
            
            2. 임베딩 생성 (Embedding Generation)
            텍스트를 벡터로 변환합니다.
            
            3. 벡터 저장소 (Vector Store)
            임베딩을 저장하고 검색합니다.
            
            4. 검색 및 생성 (Retrieval and Generation)
            질문에 맞는 문서를 찾아 답변을 생성합니다.
            """
        },
        {
            "id": "test-002", 
            "title": "청킹 전략",
            "source": "diagnostic",
            "text": """
            청킹(Chunking)은 긴 문서를 작은 단위로 나누는 과정입니다.
            
            주요 청킹 전략:
            - Sentence-based: 문장 단위로 분할
            - Paragraph-based: 단락 단위로 분할  
            - Sliding window: 고정 크기 윈도우 사용
            - Adaptive: 텍스트 특성에 따라 자동 선택
            
            적절한 청킹 전략 선택은 검색 성능에 큰 영향을 미칩니다.
            """
        }
    ]
    
    response = requests.post(
        f"{base_url}/ingest",
        json={"documents": test_docs},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Ingested {data['documentCount']} documents")
        print(f"   Created {data['ingestedChunks']} chunks")
    else:
        print(f"❌ Ingestion failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return
    
    # Wait a bit for indexing
    print("\n⏳ Waiting 2 seconds for indexing...")
    time.sleep(2)
    
    # 4. Test retrieval with different questions
    print("\n4. Testing retrieval...")
    test_questions = [
        "RAG 시스템이란 무엇인가요?",
        "청킹이란 무엇인가요?",
        "What is chunking?",
        "벡터 저장소의 역할은?",
        "임베딩 생성 과정을 설명해주세요"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n   Test {i}: {question}")
        
        response = requests.post(
            f"{base_url}/ask",
            json={"question": question},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data['answer'][:150]
            if len(data['answer']) > 150:
                answer += "..."
            
            ctx_ids = data.get('ctxIds', [])
            latency = data.get('latencyMs', 0)
            
            if ctx_ids:
                print(f"   ✅ Found {len(ctx_ids)} contexts")
                print(f"   Answer: {answer}")
                print(f"   Latency: {latency}ms")
            else:
                print(f"   ⚠️ No contexts found")
                print(f"   Answer: {answer}")
                
        else:
            print(f"   ❌ Request failed: {response.status_code}")
    
    # 5. Direct vector store check (if possible)
    print("\n5. Checking vector store directly...")
    print("   (This would require direct access to the store)")
    
    print("\n" + "="*60)
    print("Diagnostic Results:")
    print("="*60)
    print("\nPossible issues if no contexts found:")
    print("1. Vector store is not persisting data")
    print("2. Embedder dimension mismatch")
    print("3. Retriever not searching correctly")
    print("4. Query expansion issues")
    print("\nRecommended actions:")
    print("1. Check server logs for errors")
    print("2. Verify embedder is working (check for 'Model loaded' message)")
    print("3. Check if InMemoryVectorStore is actually storing chunks")
    print("4. Verify retriever.retrieve() is being called correctly")

if __name__ == "__main__":
    test_full_cycle()
