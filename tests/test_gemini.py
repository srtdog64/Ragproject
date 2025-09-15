#!/usr/bin/env python
"""
Test Gemini API directly
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.join(os.path.dirname(__file__), 'rag'))

async def test_gemini():
    from adapters.llm_client import GeminiLlm
    
    # Test different models
    models_to_test = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-pro"
    ]
    
    for model_name in models_to_test:
        print(f"\nTesting model: {model_name}")
        print("-" * 50)
        
        try:
            llm = GeminiLlm(model=model_name)
            llm._temperature = 0.7
            llm._max_tokens = 100
            
            prompt = "반가워! 한국어로 간단히 인사해줘."
            system = "You are a friendly assistant. Respond in Korean."
            
            result = await llm.generate(prompt, system)
            
            if result.isOk():
                print(f"Success: {result.getValue()[:200]}")
            else:
                print(f"Error: {result.getError()}")
                
        except Exception as e:
            print(f"Exception: {e}")
    
    print("\n" + "=" * 60)
    print("Test completed!")

if __name__ == "__main__":
    asyncio.run(test_gemini())
