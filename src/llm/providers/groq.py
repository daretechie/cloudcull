import os
import logging
from typing import Dict, Any
from groq import Groq
from ..base import BaseLLM, LLMResponse, LLMRecommendation

logger = logging.getLogger("CloudCull.LLM.Groq")

class GroqProvider(BaseLLM):
    """
    Groq Implementation for Llama 3 series.
    """
    def __init__(self, api_key: str = None):
        api_key = api_key or os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"

    def classify_instance(self, metadata: Dict[str, Any], metrics: Dict[str, Any]) -> LLMResponse:
        logger.info("Groq/Llama analyzing instance %s...", metadata.get('id', 'unknown'))
        
        system_msg = """
        You are a Cloud Cost Optimization Auditor. Analyze instance metrics and metadata.
        Output a JSON object classification (ZOMBIE vs ACTIVE).
        - ZOMBIE means the instance is likely idle and should be stopped.
        - ACTIVE means it is performing useful work.
        """
        
        user_msg = f"METADATA: {metadata}\nMETRICS: {metrics}"
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            response_format={"type": "json_object"}
        )
        
        import json
        
        # Robust JSON Extraction
        text = response.choices[0].message.content
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
                content = {"decision": "ACTIVE", "reasoning": "JSON not found in Groq response", "confidence": 0.0}
        except Exception as e:
            logger.error("Failed to parse Groq response: %s | Text: %s", e, text[:100])
            content = {"decision": "ACTIVE", "reasoning": f"Parsing failure: {e}", "confidence": 0.0}
        
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
