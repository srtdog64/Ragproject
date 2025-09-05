# adapters/llm_client.py
from __future__ import annotations
import asyncio
import os
from typing import Optional, Dict, Any
from core.result import Result
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import config

# Load environment variables
load_dotenv()


class GeminiLlm:
    """Google Gemini API client with dynamic model selection"""
    def __init__(self, apiKey: Optional[str] = None, model: Optional[str] = None):
        self._apiKey = apiKey or os.getenv("GEMINI_API_KEY")
        if not self._apiKey:
            raise ValueError("Gemini API key not found. Set GEMINI_API_KEY in .env file")
        
        # Get model from config or use default
        llm_config = config.get_section('llm')
        self._model = model or llm_config.get('model', 'gemini-pro')
        self._temperature = llm_config.get('temperature', 0.7)
        self._max_tokens = llm_config.get('max_tokens', 2048)

    def getApiKey(self) -> str:
        return self._apiKey

    def setApiKey(self, key: str) -> None:
        self._apiKey = key
    
    def setModel(self, model: str) -> None:
        self._model = model
    
    def getModel(self) -> str:
        return self._model

    async def generate(self, prompt: str, system: Optional[str] = None) -> Result[str]:
        """Generate response using Gemini API"""
        try:
            import aiohttp
            import json
            
            # Map model names to API endpoints
            model_mapping = {
                # Gemini 2.5 series (Latest)
                "gemini-2.5-flash": "gemini-2.5-flash",
                "gemini-2.5-pro": "gemini-2.5-pro",
                "gemini-2.5-flash-lite": "gemini-2.5-flash-lite",
                
                # Gemini 2.0 series
                "gemini-2.0-flash": "gemini-2.0-flash-001",
                "gemini-2.0-pro": "gemini-2.0-pro-002",
                "gemini-2.0-flash-lite": "gemini-2.0-flash-lite",
                
                # Gemini 1.5 series (Legacy)
                "gemini-1.5-flash": "gemini-1.5-flash-002",
                "gemini-1.5-pro": "gemini-1.5-pro-002",
                
                # Legacy models
                "gemini-pro": "gemini-pro",
                "gemini-pro-vision": "gemini-pro-vision"
            }
            
            api_model = model_mapping.get(self._model, self._model)
            
            # Gemini API endpoint
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{api_model}:generateContent?key={self._apiKey}"
            
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
                    "temperature": self._temperature,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": self._max_tokens,
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
    """OpenAI API client"""
    def __init__(self, apiKey: Optional[str] = None, model: Optional[str] = None):
        self._apiKey = apiKey or os.getenv("OPENAI_API_KEY")
        if not self._apiKey:
            # Return stub if no API key
            self._stub_mode = True
        else:
            self._stub_mode = False
        
        # Get model from config
        llm_config = config.get_section('llm')
        self._model = model or llm_config.get('model', 'gpt-4o-mini')  # Updated default
        self._temperature = llm_config.get('temperature', 0.7)
        self._max_tokens = llm_config.get('max_tokens', 2048)

    async def generate(self, prompt: str, system: Optional[str] = None) -> Result[str]:
        if self._stub_mode:
            await asyncio.sleep(0.01)
            return Result.ok(f"[OPENAI STUB - Set OPENAI_API_KEY to use]\n{prompt[:160]}...")
        
        try:
            import aiohttp
            import json
            
            url = "https://api.openai.com/v1/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {self._apiKey}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self._model,
                "messages": messages,
                "temperature": self._temperature,
                "max_tokens": self._max_tokens
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        text = data["choices"][0]["message"]["content"]
                        return Result.ok(text)
                    else:
                        error_text = await response.text()
                        return Result.err(f"OpenAI API error (status {response.status}): {error_text}")
                        
        except Exception as ex:
            return Result.err(f"OpenAIError: {str(ex)}")


class ClaudeLlm:
    """Claude API client"""
    def __init__(self, apiKey: Optional[str] = None, model: Optional[str] = None):
        self._apiKey = apiKey or os.getenv("ANTHROPIC_API_KEY")
        if not self._apiKey:
            self._stub_mode = True
        else:
            self._stub_mode = False
        
        # Get model from config
        llm_config = config.get_section('llm')
        self._model = model or llm_config.get('model', 'claude-3-5-sonnet-latest')  # Latest Claude model
        self._temperature = llm_config.get('temperature', 0.7)
        self._max_tokens = llm_config.get('max_tokens', 2048)

    async def generate(self, prompt: str, system: Optional[str] = None) -> Result[str]:
        if self._stub_mode:
            await asyncio.sleep(0.01)
            return Result.ok(f"[CLAUDE STUB - Set ANTHROPIC_API_KEY to use]\n{prompt[:160]}...")
        
        try:
            import aiohttp
            import json
            
            url = "https://api.anthropic.com/v1/messages"
            
            headers = {
                "x-api-key": self._apiKey,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
            
            messages = [{"role": "user", "content": prompt}]
            
            payload = {
                "model": self._model,
                "messages": messages,
                "max_tokens": self._max_tokens,
                "temperature": self._temperature
            }
            
            if system:
                payload["system"] = system
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        text = data["content"][0]["text"]
                        return Result.ok(text)
                    else:
                        error_text = await response.text()
                        return Result.err(f"Claude API error (status {response.status}): {error_text}")
                        
        except Exception as ex:
            return Result.err(f"ClaudeError: {str(ex)}")


class LlmFactory:
    """Factory for creating LLM clients based on configuration"""
    
    @staticmethod
    def create() -> Any:
        """Create LLM client based on config"""
        llm_config = config.get_section('llm')
        provider = llm_config.get('type', 'gemini')
        model = llm_config.get('model')
        
        if provider == 'gemini':
            return GeminiLlm(model=model)
        elif provider == 'openai':
            return OpenAiLlm(model=model)
        elif provider == 'claude':
            return ClaudeLlm(model=model)
        else:
            # Default to Gemini
            return GeminiLlm(model=model)
