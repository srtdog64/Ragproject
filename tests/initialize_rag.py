#!/usr/bin/env python
"""
Initialize RAG system with sample data
Run this after starting the server for the first time
"""

import requests
import json
import time

def wait_for_server():
    """Wait for server to be ready"""
    print("Waiting for server to be ready...")
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get("http://localhost:7001/health")
            if response.status_code == 200:
                print("✅ Server is ready!")
                return True
        except:
            pass
        time.sleep(1)
        print(".", end="", flush=True)
    print("\n❌ Server did not start in time")
    return False

def initialize_chunker():
    """Initialize chunker with adaptive strategy"""
    try:
        # Set strategy to adaptive
        response = requests.post(
            "http://localhost:7001/api/chunkers/strategy",
            json={"strategy": "adaptive"},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            print("✅ Chunker strategy set to 'adaptive'")
        else:
            print(f"⚠️  Chunker strategy setting returned {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to set chunker strategy: {e}")

def load_initial_documents():
    """Load initial sample documents"""
    sample_docs = [
        {
            "id": "init-001",
            "title": "RAG 시스템 소개",
            "source": "initialization",
            "text": """
            RAG(Retrieval-Augmented Generation)는 정보 검색과 텍스트 생성을 결합한 
            혁신적인 AI 기술입니다. 이 시스템은 다음과 같은 주요 구성 요소로 이루어져 있습니다:
            
            1. 문서 수집 및 처리 (Document Ingestion)
            문서를 시스템에 입력하고 적절한 크기로 분할합니다. 이 과정에서 청킹(chunking) 
            전략이 매우 중요합니다. 문서의 유형과 특성에 따라 문장 단위, 단락 단위, 
            또는 슬라이딩 윈도우 방식을 선택할 수 있습니다.
            
            2. 임베딩 생성 (Embedding Generation)
            텍스트를 수치적 벡터로 변환합니다. Sentence-BERT와 같은 모델을 사용하여 
            의미적 유사성을 계산할 수 있는 밀집 벡터를 생성합니다.
            
            3. 벡터 저장소 (Vector Store)
            생성된 임베딩을 효율적으로 저장하고 검색할 수 있는 데이터베이스입니다.
            
            4. 검색 및 생성 파이프라인
            사용자 질문을 받아 관련 문서를 검색하고, 이를 바탕으로 답변을 생성합니다.
            """
        },
        {
            "id": "init-002",
            "title": "임베딩 모델의 중요성",
            "source": "initialization",
            "text": """
            임베딩은 텍스트의 의미를 수치적으로 표현하는 방법입니다. RAG 시스템에서 
            임베딩의 품질은 전체 시스템 성능에 직접적인 영향을 미칩니다.
            
            다국어 지원:
            최신 임베딩 모델들은 여러 언어를 동시에 지원합니다. 예를 들어, 
            paraphrase-multilingual-MiniLM-L12-v2 모델은 100개 이상의 언어를 
            지원하며, 한국어와 영어를 동일한 벡터 공간에 매핑할 수 있습니다.
            
            This allows the system to handle queries in different languages and 
            retrieve relevant information regardless of the language used in the 
            original documents. The embedding models capture semantic meaning 
            rather than just lexical similarity.
            
            임베딩 차원:
            일반적으로 384차원에서 768차원의 벡터가 사용됩니다. 차원이 높을수록 
            더 많은 정보를 담을 수 있지만, 저장 공간과 계산 비용도 증가합니다.
            """
        },
        {
            "id": "init-003",
            "title": "청킹 전략의 선택",
            "source": "initialization",
            "text": """
            효과적인 청킹(chunking)은 RAG 시스템의 성능을 크게 향상시킵니다.
            
            주요 청킹 전략:
            
            1. Sentence-based Chunking
            - 문장 단위로 텍스트를 분할
            - Q&A 형식이나 대화형 컨텐츠에 적합
            - 각 청크가 완전한 의미 단위를 유지
            
            2. Paragraph-based Chunking
            - 단락 단위로 분할
            - 구조화된 문서나 매뉴얼에 이상적
            - 컨텍스트가 잘 보존됨
            
            3. Sliding Window Chunking
            - 고정 크기의 윈도우를 이동하며 분할
            - 긴 서술형 텍스트나 소설에 적합
            - 오버랩을 통해 경계 정보 손실 방지
            
            4. Adaptive Chunking
            - 텍스트 특성을 분석하여 자동으로 최적 전략 선택
            - 다양한 유형의 문서를 처리할 때 유용
            - 시스템이 스스로 판단하여 적용
            
            선택 기준:
            - 문서의 구조와 형식
            - 예상 질문의 유형
            - 검색 정확도 vs 처리 속도 균형
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
            print(f"✅ Initial documents loaded successfully")
            print(f"   - Documents: {data.get('documentCount', 0)}")
            print(f"   - Chunks created: {data.get('ingestedChunks', 0)}")
            return True
        else:
            print(f"❌ Failed to load documents: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error loading documents: {e}")
        return False

def test_system():
    """Test the system with sample queries"""
    test_queries = [
        "RAG 시스템이란 무엇인가요?",
        "What are embedding models?",
        "청킹 전략에는 어떤 것들이 있나요?",
        "How do I choose the right chunking strategy?"
    ]
    
    print("\n" + "="*60)
    print("Testing system with sample queries...")
    print("="*60)
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        try:
            response = requests.post(
                "http://localhost:7001/ask",
                json={"question": query},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data['answer'][:200]  # First 200 chars
                if len(data['answer']) > 200:
                    answer += "..."
                print(f"✅ Answer: {answer}")
                print(f"   (Latency: {data['latencyMs']}ms)")
            else:
                print(f"❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    print("="*60)
    print("RAG System Initialization")
    print("="*60)
    
    # Wait for server
    if not wait_for_server():
        print("\nPlease start the server first:")
        print("  python start_server.py")
        return
    
    print("\n1. Setting up chunker...")
    initialize_chunker()
    
    print("\n2. Loading initial documents...")
    if load_initial_documents():
        print("\n3. Testing system...")
        test_system()
    
    print("\n" + "="*60)
    print("✅ Initialization complete!")
    print("The RAG system is now ready to use.")
    print("="*60)

if __name__ == "__main__":
    main()
