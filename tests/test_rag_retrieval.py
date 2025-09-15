#!/usr/bin/env python
"""
Direct test to check if RAG retrieval is working
"""

import requests
import json

def test_rag_system():
    base_url = "http://localhost:7001"
    
    print("="*60)
    print("RAG Retrieval Test")
    print("="*60)
    
    # 1. Ingest test documents
    print("\n1. Ingesting test documents...")
    test_docs = [
        {
            "id": "test-direct-001",
            "title": "타로카드 시스템",
            "source": "test",
            "text": """
            타로카드는 78장의 카드로 구성된 점술 도구입니다.
            각 카드는 고유한 상징과 의미를 가지고 있습니다.
            메이저 아르카나 22장과 마이너 아르카나 56장으로 구성됩니다.
            타로 리딩은 과거, 현재, 미래를 통찰하는 데 사용됩니다.
            """
        },
        {
            "id": "test-direct-002",
            "title": "RAG 시스템 구조",
            "source": "test",
            "text": """
            RAG 시스템은 검색 증강 생성(Retrieval-Augmented Generation) 기술입니다.
            문서를 청킹하여 작은 단위로 나눕니다.
            각 청크를 임베딩으로 변환하여 벡터 저장소에 저장합니다.
            질문이 들어오면 관련 청크를 검색하여 컨텍스트로 사용합니다.
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
        print(f"Ingested: {data['documentCount']} docs, {data['ingestedChunks']} chunks")
    else:
        print(f"Ingestion failed: {response.status_code}")
        return
    
    # 2. Test queries
    print("\n2. Testing retrieval...")
    test_queries = [
        "타로카드란 무엇인가요?",
        "RAG 시스템이 뭐야?",
        "청킹이란?",
        "메이저 아르카나는 몇 장인가요?"
    ]
    
    for i, question in enumerate(test_queries, 1):
        print(f"\n   Query {i}: {question}")
        
        response = requests.post(
            f"{base_url}/ask",
            json={"question": question},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data['answer'][:100] + "..." if len(data['answer']) > 100 else data['answer']
            ctx_ids = data.get('ctxIds', [])
            
            print(f"   Contexts found: {len(ctx_ids)}")
            print(f"   Answer: {answer}")
            
            if not ctx_ids:
                print("   NO CONTEXTS RETRIEVED!")
        else:
            print(f"   Request failed: {response.status_code}")
    
    print("\n" + "="*60)
    print("Check server logs for detailed information:")
    print("- QueryExpansionStep logs")
    print("- RetrieveStep logs")
    print("- VectorRetriever logs")
    print("- InMemoryVectorStore logs")
    print("="*60)

if __name__ == "__main__":
    test_rag_system()
