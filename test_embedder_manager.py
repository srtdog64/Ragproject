#!/usr/bin/env python
"""
Migration helper to transition from old embedder to new manager-based system
"""
import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.adapters.embedders.manager import EmbedderManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_embedder_manager():
    """Test the new embedder manager system"""
    
    print("=" * 60)
    print("Testing Embedder Manager System")
    print("=" * 60)
    
    # Load manager from YAML
    manager = EmbedderManager.fromYaml("config/embeddings.yml")
    
    # Test texts
    english_texts = [
        "This is an English sentence about RAG systems.",
        "Machine learning is transforming document retrieval."
    ]
    
    korean_texts = [
        "한국어 문서 검색 시스템입니다.",
        "임베딩 모델이 다국어를 지원합니다."
    ]
    
    mixed_texts = [
        "This is mixed: 한국어와 English",
        "RAG 시스템은 very powerful합니다."
    ]
    
    # Test auto-selection
    print("\n1. Testing auto-selection policy:")
    print("-" * 40)
    
    for name, texts in [("English", english_texts), 
                        ("Korean", korean_texts), 
                        ("Mixed", mixed_texts)]:
        embedder, sig = manager.resolve("auto", texts)
        print(f"{name} texts -> {embedder.getName()} (dim={embedder.getDim()})")
        
        # Test embedding
        embeddings = embedder.embedTexts(texts[:1])
        print(f"  Sample embedding shape: [{len(embeddings)}][{len(embeddings[0])}]")
        print(f"  Namespace: {manager.namespaceFor(sig)}")
    
    # Test specific profiles
    print("\n2. Testing specific profiles:")
    print("-" * 40)
    
    for profile in ["multilingual_minilm", "all_minilm", "fallback_384"]:
        try:
            embedder, sig = manager.resolve(profile, [])
            print(f"{profile}: {embedder.getName()} (dim={embedder.getDim()})")
        except Exception as e:
            print(f"{profile}: ERROR - {e}")
    
    print("\n3. Testing dimension validation:")
    print("-" * 40)
    
    embedder, _ = manager.resolve("all_minilm", [])
    result = manager.ensureDim(384, embedder)
    print(f"Dimension check (384 == {embedder.getDim()}): {'OK' if result.ok else result.error}")
    
    result = manager.ensureDim(768, embedder)
    print(f"Dimension check (768 == {embedder.getDim()}): {'OK' if result.ok else result.error}")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    test_embedder_manager()
