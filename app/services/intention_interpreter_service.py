import logging
from typing import Dict, Any
from app.services.ai_service import AsyncAIService

logger = logging.getLogger(__name__)


class IntentionInterpreterService:
    def __init__(self, ai_service: AsyncAIService):
        self.ai_service = ai_service

    async def analyze_intention(self, user_profile: Dict[str, Any], target_person_profile: Dict[str, Any], use_case: str) -> Dict[str, Any]:
        """
        Analyze the intention of a target person based on user profile, target profile, and specific use case.
        Uses clinical psychological assessment framework.
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
            
            # Parse the AI response - extract the response text from the AI service result
            ai_response_text = ai_result.get("response", "")
            logger.info(f"AI Response Text: {ai_response_text[:200]}...")  # Log first 200 chars
            return self._parse_ai_response(ai_response_text)
            
        except Exception as e:
            return {
                "success": False,
                "error": f"AI analysis failed: {str(e)}",
                "intention": "unknown",
                "rationale": [],
                "reflective_question": "What aspects of this situation would you like to explore further?"
            }

    def _build_analysis_prompt(self, user_profile: Dict[str, Any], target_person_profile: Dict[str, Any], use_case: str) -> str:
        """Build a comprehensive prompt for the AI analysis."""
        
        prompt = f"""
You are an expert clinical psychologist and psychotherapist specializing in intention interpretation and psycho-social-bio assessment, with expertise in evidence-based therapeutic interventions. 
Your task is to analyze the intention behind a specific behavior or statement based on the provided profiles and context, using clinical psychological frameworks.

IMPORTANT: Analyze ALL details provided in the profiles, including any negative behaviors, personality traits, or concerning patterns mentioned.

USER PROFILE:
{user_profile.get('profile', 'Not provided')}

TARGET PERSON PROFILE:
{target_person_profile.get('profile', 'Not provided')}

SPECIFIC USE CASE/SITUATION:
{use_case}

Please analyze the target person's intention using the following clinical framework:

1. INTENTION ASSESSMENT:
   - Determine if the intention is POSITIVE, NEGATIVE, or NEUTRAL
   - AUTOMATICALLY FLAG AS NEGATIVE if the target person profile contains keywords like: "bully", "bullying", "drugs", "drug use", "aggressive", "violent", "manipulative", "toxic", "abusive", "harmful", "dangerous", "negative behavior", "concerning", "red flag"
   - Consider the person's psychological state, social context, and behavioral patterns
   - If negative behaviors are present, the intention should reflect the concerning nature of their actions
   - Consider whether words and actions are consistent or if there's a disconnect
   - Evaluate the impact on human dignity and respect for others

2. RATIONALE:
   - Provide 3-5 bullet points explaining your interpretation using clinical psychological concepts
   - Each point should reference specific psychological theories, research, or theoretical frameworks
   - Include citations to relevant psychological theories (e.g., "According to Bowlby's attachment theory...", "Research by Bandura on social learning suggests...", "Cognitive behavioral theory indicates...")
   - Reference specific behaviors, personality traits, or social dynamics mentioned in the profiles
   - Pay special attention to any concerning behaviors, negative patterns, or red flags mentioned
   - If negative behaviors are detected (bullying, drug use, aggression, etc.), emphasize these in your analysis
   - Pay special attention to inconsistencies between what people say and how they act
   - Evaluate whether actions align with stated intentions or if there's a disconnect
   - Always consider human dignity and respect in your analysis
   - Use clinical terminology to describe concerning patterns and their psychological implications
   - Consider psychological patterns, attachment theory, interpersonal dynamics, and other relevant frameworks
   - Use appropriate clinical terminology and psychological frameworks

3. REFLECTIVE QUESTION:
   - End with an open-ended question that prompts the user to think about the analysis
   - The question should encourage deeper reflection on the situation
   - Make it thought-provoking and relevant to the specific context

Please respond in the following JSON format:
{{
    "intention": "positive/negative/neutral",
    "rationale": [
        "Clinical psychological analysis point 1 with theoretical source (e.g., 'According to [Theory Name]...')",
        "Clinical psychological analysis point 2 with theoretical source (e.g., 'Research by [Author/Theory] suggests...')", 
        "Clinical psychological analysis point 3 with theoretical source (e.g., 'From a [Framework] perspective...')"
    ],
    "reflective_question": "An open-ended question to prompt deeper thinking about this situation"
}}

Focus on being clinically accurate, evidence-based, and academically rigorous. Use appropriate psychological terminology, cite specific theories and research, and consider the complexity of human behavior through established clinical psychological frameworks.
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
