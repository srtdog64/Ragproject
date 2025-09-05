#!/usr/bin/env python
"""
Quick test script to verify chunking strategies work correctly
"""

import sys
import os
sys.path.append('E:/Ragproject/rag')

from core.types import Document
from chunkers.registry import registry
from chunkers.wrapper import ChunkerWrapper

def test_chunking():
    """Test all chunking strategies"""
    
    # Test document
    test_doc = Document(
        id="test1",
        title="Test Document",
        source="test",
        text="""
        RAG 시스템은 검색 기반 생성 모델입니다. 이 시스템은 문서를 작은 청크로 나누어 벡터 데이터베이스에 저장합니다.
        
        사용자 질문이 들어오면, 먼저 관련 문서 조각을 검색합니다. 그 다음 검색된 내용을 기반으로 LLM이 답변을 생성합니다.
        
        청킹 전략은 RAG 시스템의 핵심 요소입니다. 문장 단위, 문단 단위, 슬라이딩 윈도우 등 다양한 전략이 있습니다.
        각 전략마다 장단점이 있어 문서 특성에 맞게 선택해야 합니다.
        """
    )
    
    print("=" * 60)
    print("Testing Chunking Strategies")
    print("=" * 60)
    
    # Test wrapper
    print("\n1. Testing ChunkerWrapper...")
    wrapper = ChunkerWrapper()
    
    strategies = registry.list_strategies()
    for strategy_info in strategies:
        strategy_name = strategy_info['name']
        print(f"\n📦 Testing {strategy_name}: {strategy_info['description']}")
        
        # Set strategy
        registry.set_strategy(strategy_name)
        
        # Chunk using wrapper (compatible with old interface)
        try:
            chunks = wrapper.chunk(test_doc)
            print(f"   ✅ Generated {len(chunks)} chunks")
            
            # Show first chunk preview
            if chunks:
                first_chunk = chunks[0]
                preview = first_chunk.text[:100] + "..." if len(first_chunk.text) > 100 else first_chunk.text
                print(f"   Preview: {preview}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
    
    # Reset to default
    registry.set_strategy("adaptive")
    print("\n📌 Reset to default strategy: adaptive")

if __name__ == "__main__":
    test_chunking()
