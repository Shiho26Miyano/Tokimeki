import logging
import hashlib
import json
from typing import Dict, Any
from app.services.ai_service import AsyncAIService

logger = logging.getLogger(__name__)


class IntentionInterpreterService:
    def __init__(self, ai_service: AsyncAIService):
        self.ai_service = ai_service

    async def analyze_intention(self, user_profile: Dict[str, Any], target_person_profile: Dict[str, Any], use_case: str) -> Dict[str, Any]:
        """
        Analyze the intention of a target person based on user profile, target profile, and specific use case.
        Uses clinical psychological assessment framework with caching for speed.
        """
        
        # Generate cache key for this analysis
        cache_key = self._generate_cache_key(user_profile, target_person_profile, use_case)
        
        # Check if we have a cached result
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            logger.info("Returning cached analysis result")
            return cached_result
        
        # Construct the structured prompt for the AI
        structured_prompt = self._build_analysis_prompt(user_profile, target_person_profile, use_case)
        
        try:
            # Call the AI service with optimized parameters for speed
            ai_result = await self.ai_service.chat(
                message=structured_prompt,
                model="mistral-small",
                temperature=0.1,  # Lower temperature for more consistent, faster responses
                max_tokens=800    # Reduced from 2000 for faster generation
            )
            
            # Parse the AI response - extract the response text from the AI service result
            ai_response_text = ai_result.get("response", "")
            logger.info(f"AI Response Text: {ai_response_text[:200]}...")  # Log first 200 chars
            
            # Parse and cache the result
            result = self._parse_ai_response(ai_response_text)
            if result.get("success"):
                self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"AI analysis failed: {str(e)}",
                "intention": "unknown",
                "rationale": [],
                "reflective_question": "What aspects of this situation would you like to explore further?"
            }

    def _build_analysis_prompt(self, user_profile: Dict[str, Any], target_person_profile: Dict[str, Any], use_case: str) -> str:
        """Build an optimized prompt for faster AI analysis."""
        
        prompt = f"""You are a clinical psychologist analyzing intentions. Assess the target person's behavior:

USER: {user_profile.get('profile', 'Not provided')}
TARGET: {target_person_profile.get('profile', 'Not provided')}
SITUATION: {use_case}

Analyze using:
1. INTENTION: POSITIVE/NEGATIVE/NEUTRAL (flag as NEGATIVE if profile mentions: bully, drugs, aggressive, manipulative, toxic, abusive)
2. RATIONALE: 3 brief points with psychological theory references
3. REFLECTIVE QUESTION: One thought-provoking question

Respond in JSON:
{{
    "intention": "positive/negative/neutral",
    "rationale": [
        "Point 1 with theory reference",
        "Point 2 with theory reference", 
        "Point 3 with theory reference"
    ],
    "reflective_question": "Your question here"
}}"""
        return prompt

    def _generate_cache_key(self, user_profile: Dict[str, Any], target_person_profile: Dict[str, Any], use_case: str) -> str:
        """Generate a unique cache key for the analysis."""
        content = f"{user_profile.get('profile', '')}{target_person_profile.get('profile', '')}{use_case}"
        return f"intention_analysis:{hashlib.md5(content.encode()).hexdigest()}"

    def _get_cached_result(self, cache_key: str) -> Dict[str, Any]:
        """Get cached result if available."""
        # Simple in-memory cache for now - can be enhanced with Redis later
        if not hasattr(self, '_cache'):
            self._cache = {}
        
        cached = self._cache.get(cache_key)
        if cached:
            # Check if cache is still valid (24 hours)
            import time
            if time.time() - cached.get('timestamp', 0) < 86400:  # 24 hours
                return cached.get('data')
            else:
                # Remove expired cache
                del self._cache[cache_key]
        return None

    def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """Cache the analysis result."""
        if not hasattr(self, '_cache'):
            self._cache = {}
        
        import time
        self._cache[cache_key] = {
            'data': result,
            'timestamp': time.time()
        }
        logger.info(f"Cached analysis result for key: {cache_key}")

    def _parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """Parse the AI response and extract the structured information."""
        
        try:
            # Try to extract JSON from the response
            import json
            import re
            
            # Look for JSON content in the response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                
                return {
                    "success": True,
                    "intention": parsed.get("intention", "unknown"),
                    "rationale": parsed.get("rationale", []),
                    "reflective_question": parsed.get("reflective_question", "No reflective question provided.")
                }
            else:
                # Fallback parsing if JSON extraction fails
                return {
                    "success": True,
                    "intention": "neutral",
                    "rationale": ["AI response received but could not be parsed in expected format"],
                    "reflective_question": "How does this analysis resonate with your understanding of the situation?"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse AI response: {str(e)}",
                "intention": "unknown",
                "rationale": []
            }
