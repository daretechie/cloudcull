import os
import logging
from typing import Dict, Any
from google import genai
from ..base import BaseLLM, LLMResponse, LLMRecommendation

logger = logging.getLogger("CloudCull.LLM.Google")

class GoogleProvider(BaseLLM):
    """
    Google Implementation for Gemini 1.5/2.0 series using the modern google-genai SDK.
    """
    def __init__(self, api_key: str = None):
        from ...core.settings import settings
        api_key = api_key or settings.google_api_key
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash"

    def classify_instance(self, metadata: Dict[str, Any], metrics: Dict[str, Any]) -> LLMResponse:
        logger.info("Gemini analyzing instance %s...", metadata.get('id', 'unknown'))
        
        system_instruction = """
        You are a Cloud FinOps Specialist. Classify a GPU instance as 'ZOMBIE' or 'ACTIVE' based on its utilization.
        
        RULES:
        - ZOMBIE: Max CPU < 5%, Network TX/RX < 1MB.
        - ACTIVE: Significant load or iterative compute.
        
        Required JSON Response:
        {
          "decision": "ZOMBIE" | "ACTIVE",
          "reasoning": "step-by-step logic",
          "confidence": 0.0-1.0
        }
        """
        
        from ..utils import sanitize_for_prompt
        safe_metadata = sanitize_for_prompt(metadata)
        safe_metrics = sanitize_for_prompt(metrics)
        
        user_input = f"METADATA: {safe_metadata}\nMETRICS: {safe_metrics}"
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=user_input,
            config={
                'system_instruction': system_instruction,
                'response_mime_type': 'application/json'
            }
        )
        
        import json
        
        # Robust JSON Extraction
        text = response.text
        content = {}
        try:
            # Clean up potential markdown formatting
            text_clean = text.strip()
            if text_clean.startswith("```"):
                lines = text_clean.splitlines()
                if len(lines) >= 3:
                    text_clean = "\n".join(lines[1:-1])
            
            # Find the JSON object
            start_idx = text_clean.find('{')
            end_idx = text_clean.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = text_clean[start_idx : end_idx + 1]
                content = json.loads(json_str)
            else:
                content = {"decision": "ACTIVE", "reasoning": "JSON not found in Gemini response", "confidence": 0.0}
        except Exception as e:
            logger.error("Failed to parse Gemini response: %s | Text: %s", e, text[:100])
            content = {"decision": "ACTIVE", "reasoning": f"Parsing failure: {e}", "confidence": 0.0}
        
        recommendation = LLMRecommendation(
            decision=content.get("decision", "ACTIVE"),
            reasoning=content.get("reasoning", text[:500]),
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
