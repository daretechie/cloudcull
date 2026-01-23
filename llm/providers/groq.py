import os
import logging
from typing import Dict, Any
from groq import Groq
from llm.base import BaseLLM, LLMResponse, LLMRecommendation

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
        
        prompt = f"Analyze: {metadata} Metrics: {metrics}. Output JSON with decision, reasoning, confidence."
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        import json
        content = json.loads(response.choices[0].message.content)
        
        recommendation = LLMRecommendation(
            decision=content.get("decision", "ACTIVE"),
            reasoning=content.get("reasoning", response.choices[0].message.content),
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
