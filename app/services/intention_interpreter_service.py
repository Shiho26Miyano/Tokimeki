from typing import Dict, Any
from app.services.ai_service import AsyncAIService


class IntentionInterpreterService:
    def __init__(self, ai_service: AsyncAIService):
        self.ai_service = ai_service

    async def analyze_intention(self, user_profile: Dict[str, Any], target_person_profile: Dict[str, Any], use_case: str) -> Dict[str, Any]:
        """
        Analyze the intention of a target person based on user profile, target profile, and specific use case.
        Uses DSM-5 related criteria and psycho-social-bio assessment framework.
        """
        
        # Construct the structured prompt for the AI
        structured_prompt = self._build_analysis_prompt(user_profile, target_person_profile, use_case)
        
        try:
            # Call the AI service with mistral-small model
            ai_result = await self.ai_service.chat(
                message=structured_prompt,
                model="mistral-small",
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse the AI response
            return self._parse_ai_response(ai_result)
            
        except Exception as e:
            return {
                "success": False,
                "error": f"AI analysis failed: {str(e)}",
                "intention": "unknown",
                "rationale": [],
                "advice": "Unable to analyze intention at this time. Please try again."
            }

    def _build_analysis_prompt(self, user_profile: Dict[str, Any], target_person_profile: Dict[str, Any], use_case: str) -> str:
        """Build a comprehensive prompt for the AI analysis."""
        
        prompt = f"""
You are an expert psychologist specializing in intention interpretation and psycho-social-bio assessment. 
Your task is to analyze the intention behind a specific behavior or statement based on the provided profiles and context.

USER PROFILE:
{user_profile.get('profile', 'Not provided')}

TARGET PERSON PROFILE:
{target_person_profile.get('profile', 'Not provided')}

SPECIFIC USE CASE/SITUATION:
{use_case}

Please analyze the target person's intention using the following framework:

1. INTENTION ASSESSMENT:
   - Determine if the intention is POSITIVE, NEGATIVE, or NEUTRAL
   - Consider the person's psychological state, social context, and behavioral patterns

2. RATIONALE:
   - Provide 3-5 bullet points explaining your interpretation
   - Reference specific behaviors, personality traits, or social dynamics
   - Consider DSM-5 related psychological patterns if applicable

3. ADVICE:
   - Provide positive, warm, and kind advice to the user
   - Focus on personal growth and better life outcomes
   - Even if the intention is negative, frame advice constructively

Please respond in the following JSON format:
{{
    "intention": "positive/negative/neutral",
    "rationale": [
        "Point 1 about the person's behavior or personality",
        "Point 2 about social dynamics or context",
        "Point 3 about psychological patterns or motivations"
    ],
    "advice": "Your warm and constructive advice here"
}}

Focus on being empathetic, accurate, and helpful. Consider the complexity of human behavior and avoid oversimplification.
"""
        return prompt

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
                    "advice": parsed.get("advice", "No specific advice provided.")
                }
            else:
                # Fallback parsing if JSON extraction fails
                return {
                    "success": True,
                    "intention": "neutral",
                    "rationale": ["AI response received but could not be parsed in expected format"],
                    "advice": "Please review the analysis and consider the context carefully."
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse AI response: {str(e)}",
                "intention": "unknown",
                "rationale": [],
                "advice": "Unable to process the analysis results. Please try again."
            }
