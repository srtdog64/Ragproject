# adapters/llm_client.py
from __future__ import annotations
import asyncio
import os
from typing import Optional
from core.result import Result
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class GeminiLlm:
    """Google Gemini API client"""
    def __init__(self, apiKey: Optional[str] = None):
        self._apiKey = apiKey or os.getenv("GEMINI_API_KEY")
        if not self._apiKey:
            raise ValueError("Gemini API key not found. Set GEMINI_API_KEY in .env file")

    def getApiKey(self) -> str:
        return self._apiKey

    def setApiKey(self, key: str) -> None:
        self._apiKey = key

    async def generate(self, prompt: str, system: Optional[str] = None) -> Result[str]:
        """Generate response using Gemini API"""
        try:
            import aiohttp
            import json
            
            # Gemini API endpoint
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={self._apiKey}"
            
            # Combine system message and prompt if system is provided
            if system:
                full_prompt = f"{system}\n\n{prompt}"
            else:
                full_prompt = prompt
            
            # Request payload
            payload = {
                "contents": [{
                    "parts": [{
                        "text": full_prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 1024,
                }
            }
            
            # Make async request
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Extract text from Gemini response
                        try:
                            text = data["candidates"][0]["content"]["parts"][0]["text"]
                            return Result.ok(text)
                        except (KeyError, IndexError) as e:
                            return Result.err(f"Failed to parse Gemini response: {str(e)}")
                    else:
                        error_text = await response.text()
                        return Result.err(f"Gemini API error (status {response.status}): {error_text}")
                        
        except Exception as ex:
            return Result.err(f"GeminiError: {str(ex)}")


class OpenAiLlm:
    """OpenAI API client (stub)"""
    def __init__(self, apiKey: str):
        self._apiKey = apiKey

    def getApiKey(self) -> str:
        return self._apiKey

    def setApiKey(self, key: str) -> None:
        self._apiKey = key

    async def generate(self, prompt: str, system: Optional[str] = None) -> Result[str]:
        try:
            # This is a stub - replace with actual OpenAI API call if needed
            await asyncio.sleep(0.01)
            return Result.ok(f"[OPENAI STUB - Set OpenAI API key to use]\n{prompt[:160]}...")
        except Exception as ex:
            return Result.err(f"OpenAIError: {ex}")


class ClaudeLlm:
    """Claude API client (stub)"""
    def __init__(self, apiKey: str):
        self._apiKey = apiKey

    def getApiKey(self) -> str:
        return self._apiKey

    def setApiKey(self, key: str) -> None:
        self._apiKey = key

    async def generate(self, prompt: str, system: Optional[str] = None) -> Result[str]:
        try:
            # This is a stub - replace with actual Claude API call if needed
            await asyncio.sleep(0.01)
            return Result.ok(f"[CLAUDE STUB - Set Claude API key to use]\n{prompt[:160]}...")
        except Exception as ex:
            return Result.err(f"ClaudeError: {ex}")
