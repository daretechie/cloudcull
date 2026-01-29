import os
import logging
from typing import Dict, Any
from openai import OpenAI
from ..base import BaseLLM, LLMResponse, LLMRecommendation

logger = logging.getLogger("CloudCull.LLM.OpenAI")

class OpenAIProvider(BaseLLM):
    """
    OpenAI Implementation for GPT-4 series.
    """
    def __init__(self, api_key: str = None):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o" 

    def classify_instance(self, metadata: Dict[str, Any], metrics: Dict[str, Any]) -> LLMResponse:
        logger.info("GPT-4 analyzing instance %s...", metadata.get('id', 'unknown'))
        
        system_msg = """
        You are a Cloud Infrastructure Sniper. Analyze instance state and decide if it is a 'ZOMBIE' (idle waste) or 'ACTIVE'.
        
        RULES:
        1. If Max CPU is < 2% and Network is < 0.1MB, classify as ZOMBIE.
        2. If Metadata indicates 'production' or 'critical', be more conservative.
        
        Response MUST be a JSON object with keys: decision, reasoning, confidence.
        """
        
        # Prompt Injection Protection: Sanitize metadata keys and values
        def sanitize(obj):
            if isinstance(obj, dict):
                return {str(k)[:100]: sanitize(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [sanitize(i) for i in obj]
            elif isinstance(obj, str):
                return obj[:1000].replace("{", "[").replace("}", "]") # Neutralize potential JSON injection
            return obj

        safe_metadata = sanitize(metadata)
        safe_metrics = sanitize(metrics)
        
        user_msg = f"METADATA: {safe_metadata}\nMETRICS: {safe_metrics}"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                response_format={"type": "json_object"}
            )
            
            # Robust JSON Extraction (Improved)
            from ..utils import extract_json_from_text
            text = response.choices[0].message.content
            content = extract_json_from_text(text)

            if not content:
                logger.error("Failed to parse OpenAI response: JSON extraction empty | Text: %s", text[:100])
                content = {"decision": "ACTIVE", "reasoning": "Failed to parse structured response", "confidence": 0.0}
            
            recommendation = LLMRecommendation(
                decision=content.get("decision", "ACTIVE"),
                reasoning=content.get("reasoning", text[:500]),
                confidence=content.get("confidence", 0.5)
            )
            
            return LLMResponse(
                raw_response=response.choices[0].message.content,
                recommendation=recommendation,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens
                },
                model=self.model
            )
        except Exception as e:
            logger.error("OpenAI classification failed: %s", e)
            return LLMResponse(
                raw_response=str(e),
                recommendation=LLMRecommendation(decision="ACTIVE", reasoning="API Error", confidence=0.0),
                usage={},
                model=self.model
            )
