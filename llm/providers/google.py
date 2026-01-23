import os
import logging
from typing import Dict, Any
from google import genai
from llm.base import BaseLLM, LLMResponse, LLMRecommendation

logger = logging.getLogger("CloudCull.LLM.Google")

class GoogleProvider(BaseLLM):
    """
    Google Implementation for Gemini 1.5/2.0 series using the modern google-genai SDK.
    """
    def __init__(self, api_key: str = None):
        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash"

    def classify_instance(self, metadata: Dict[str, Any], metrics: Dict[str, Any]) -> LLMResponse:
        logger.info("Gemini analyzing instance %s...", metadata.get('id', 'unknown'))
        
        prompt = f"Analyze instance: {metadata}, Metrics: {metrics}. Output decision (ZOMBIE/ACTIVE), reasoning, confidence in JSON."
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        
        import json
        content = json.loads(response.text)
        
        recommendation = LLMRecommendation(
            decision=content.get("decision", "ACTIVE"),
            reasoning=content.get("reasoning", response.text),
            confidence=content.get("confidence", 0.5)
        )
        
        return LLMResponse(
            raw_response=response.text,
            recommendation=recommendation,
            usage={
                "prompt_token_count": response.usage_metadata.prompt_token_count,
                "candidates_token_count": response.usage_metadata.candidates_token_count
            },
            model=self.model
        )
