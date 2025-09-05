#!/usr/bin/env python
# test_chunking.py
"""
Real-time Chunking Strategy Test Script
Usage: python test_chunking.py
"""

import sys
import json
import requests
from typing import Optional

class ChunkingTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        
    def list_strategies(self):
        """List all available strategies"""
        try:
            resp = requests.get(f"{self.base_url}/api/chunkers/strategies")
            data = resp.json()
            print("\n=== Available Chunking Strategies ===")
            for strategy in data['strategies']:
                status = "✓ ACTIVE" if strategy['active'] else "  "
                print(f"{status} {strategy['name']:20} - {strategy['description']}")
            print(f"\nCurrent strategy: {data['current']}")
        except Exception as e:
            print(f"Error: {e}")
    
    def get_params(self):
        """Get current parameters"""
        try:
            resp = requests.get(f"{self.base_url}/api/chunkers/params")
            params = resp.json()
            print("\n=== Current Parameters ===")
            for key, value in params.items():
                print(f"  {key:20}: {value}")
        except Exception as e:
            print(f"Error: {e}")
    
    def set_strategy(self, strategy: str):
        """Set chunking strategy"""
        try:
            resp = requests.post(
                f"{self.base_url}/api/chunkers/strategy",
                json={"strategy": strategy}
            )
            if resp.status_code == 200:
                data = resp.json()
                print(f"✓ Strategy changed to: {data['strategy']}")
            else:
                print(f"✗ Error: {resp.json().get('detail', 'Unknown error')}")
        except Exception as e:
            print(f"Error: {e}")
    
    def set_params(self, **kwargs):
        """Update parameters"""
        try:
            resp = requests.post(
                f"{self.base_url}/api/chunkers/params",
                json=kwargs
            )
            if resp.status_code == 200:
                data = resp.json()
                print("✓ Parameters updated:")
                for key, value in data['params'].items():
                    print(f"  {key}: {value}")
            else:
                print(f"✗ Error: {resp.json().get('detail', 'Unknown error')}")
        except Exception as e:
            print(f"Error: {e}")
    
    def test_chunking(self, text: str, strategy: Optional[str] = None):
        """Test chunking with sample text"""
        sample_text = """
RAG (Retrieval-Augmented Generation)는 검색 기반 생성 모델입니다.
이 시스템은 문서를 작은 청크로 나누어 벡터 데이터베이스에 저장합니다.

사용자 질문이 들어오면, 먼저 관련 문서 조각을 검색합니다.
그 다음 검색된 내용을 기반으로 LLM이 답변을 생성합니다.

청킹 전략은 RAG 시스템의 핵심 요소입니다.
문장 단위, 문단 단위, 슬라이딩 윈도우 등 다양한 전략이 있습니다.
각 전략마다 장단점이 있어 문서 특성에 맞게 선택해야 합니다.
"""
        
        # Use provided text or sample
        text_to_chunk = text if text else sample_text
        
        print(f"\n=== Testing Chunking {'with ' + strategy if strategy else 'with current strategy'} ===")
        print(f"Text length: {len(text_to_chunk)} characters")
        
        # Simulate chunking (in real scenario, would call the actual chunking endpoint)
        # For now, just show the configuration
        self.get_params()
        
        print("\nNote: To see actual chunks, integrate with the ingestion endpoint.")
    
    def interactive_menu(self):
        """Interactive menu for testing"""
        while True:
            print("\n" + "="*50)
            print("RAG Chunking Strategy Manager")
            print("="*50)
            print("1. List all strategies")
            print("2. Get current parameters")
            print("3. Change strategy")
            print("4. Update parameters")
            print("5. Test with sample text")
            print("6. Server health check")
            print("0. Exit")
            
            choice = input("\nSelect option: ").strip()
            
            if choice == "1":
                self.list_strategies()
            
            elif choice == "2":
                self.get_params()
            
            elif choice == "3":
                self.list_strategies()
                strategy = input("\nEnter strategy name: ").strip()
                if strategy:
                    self.set_strategy(strategy)
            
            elif choice == "4":
                print("\nAvailable parameters:")
                print("  - maxTokens (int)")
                print("  - windowSize (int)")
                print("  - overlap (int)")
                print("  - semanticThreshold (float)")
                print("  - language (str)")
                print("  - sentenceMinLen (int)")
                print("  - paragraphMinLen (int)")
                
                params = {}
                while True:
                    param = input("\nParameter name (or press Enter to finish): ").strip()
                    if not param:
                        break
                    value = input(f"Value for {param}: ").strip()
                    
                    # Try to parse value type
                    try:
                        if '.' in value:
                            params[param] = float(value)
                        elif value.isdigit():
                            params[param] = int(value)
                        else:
                            params[param] = value
                    except:
                        params[param] = value
                
                if params:
                    self.set_params(**params)
            
            elif choice == "5":
                self.test_chunking("")
            
            elif choice == "6":
                try:
                    resp = requests.get(f"{self.base_url}/health")
                    print(f"\n✓ Server status: {resp.json()}")
                except:
                    print("\n✗ Server is not responding")
            
            elif choice == "0":
                print("\nGoodbye!")
                break
            
            else:
                print("\n✗ Invalid option")

def main():
    print("""
╔════════════════════════════════════════════╗
║   RAG Real-time Chunking Strategy Manager  ║
╚════════════════════════════════════════════╝
    """)
    
    # Check if server is running
    try:
        resp = requests.get("http://localhost:8000/health")
        if resp.status_code == 200:
            print("✓ Server is running")
    except:
        print("⚠ Warning: Server is not responding at http://localhost:8000")
        print("  Please start the server with: python server.py")
        
    tester = ChunkingTester()
    
    # Show initial status
    tester.list_strategies()
    
    # Start interactive menu
    tester.interactive_menu()

if __name__ == "__main__":
    main()
