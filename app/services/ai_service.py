import httpx
import asyncio
import logging
from typing import Dict, Any, List, Optional
from ..core.config import settings, FREE_MODELS
from .cache_service import AsyncCacheService

logger = logging.getLogger(__name__)

class AsyncAIService:
    def __init__(self, http_client: httpx.AsyncClient, cache_service: AsyncCacheService):
        self.http_client = http_client
        self.cache_service = cache_service
        self.api_key = settings.openrouter_api_key
        self.api_url = settings.openrouter_api_url
        
        logger.info(f"AI Service initialized with API key: {self.api_key[:20] + '...' if self.api_key else 'None'}")
        
        if not self.api_key:
            logger.warning("OpenRouter API key not configured")
    
    async def call_api(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "mistral-small", 
        temperature: float = 0.7, 
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """Make async API call to OpenRouter"""
        
        logger.info(f"Calling API with key: {self.api_key[:20] + '...' if self.api_key else 'None'}")
        
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")
        
        if model not in FREE_MODELS:
            raise ValueError(f"Invalid model: {model}")
        
        # Generate cache key
        cache_key = f"ai_api:{model}:{hash(str(messages) + str(temperature) + str(max_tokens))}"
        
        # Check cache first
        cached_response = await self.cache_service.get(cache_key)
        if cached_response:
            logger.info(f"Cache hit for AI API call: {model}")
            return cached_response
        
        # Prepare request
        payload = {
            "model": FREE_MODELS[model],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            logger.info(f"Making API call to {model}")
            response = await self.http_client.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                # Cache successful response
                await self.cache_service.set(cache_key, result, ttl=300)
                return result
            else:
                error_msg = f"API call failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except httpx.TimeoutException:
            error_msg = "API call timed out"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            logger.error(f"API call error: {e}")
            raise
    
    async def compare_models(
        self, 
        prompt: str, 
        models: List[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> List[Dict[str, Any]]:
        """Compare multiple models concurrently"""
        
        if models is None:
            models = ["mistral-small", "deepseek-chat", "qwen3-8b"]
        
        # Validate models
        for model in models:
            if model not in FREE_MODELS:
                raise ValueError(f"Invalid model: {model}")
        
        # Create tasks for concurrent execution
        tasks = []
        for model in models:
            messages = [{"role": "user", "content": prompt}]
            task = self.call_api(messages, model, temperature, max_tokens)
            tasks.append(task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "model": models[i],
                    "error": str(result),
                    "success": False
                })
            else:
                processed_results.append({
                    "model": models[i],
                    "response": result.get("choices", [{}])[0].get("message", {}).get("content", ""),
                    "usage": result.get("usage", {}),
                    "success": True
                })
        
        return processed_results
    
    async def chat(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]] = None,
        model: str = "mistral-small",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """Chat with AI model"""
        
        # Build messages list
        messages = []
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({"role": "user", "content": message})
        
        # Make API call
        result = await self.call_api(messages, model, temperature, max_tokens)
        
        # Extract response
        response_content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Update conversation history
        if conversation_history is None:
            conversation_history = []
        
        conversation_history.append({"role": "user", "content": message})
        conversation_history.append({"role": "assistant", "content": response_content})
        
        return {
            "response": response_content,
            "model": model,
            "usage": result.get("usage", {}),
            "conversation_history": conversation_history
        }
    
    async def get_available_models(self) -> List[Dict[str, str]]:
        """Get list of available models"""
        return [
            {"id": model_id, "name": model_name} 
            for model_id, model_name in FREE_MODELS.items()
        ] 