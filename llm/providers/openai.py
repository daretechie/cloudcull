import os
import logging
from typing import Dict, Any
from openai import OpenAI
from llm.base import BaseLLM, LLMResponse, LLMRecommendation

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
        
        prompt = f"""
        Analyze this cloud instance state and decide if it is a 'ZOMBIE' (idle waste) or 'ACTIVE' (useful).
        
        METADATA: {metadata}
        METRICS: {metrics}
        
        Return JSON with:
        - decision: 'ZOMBIE' or 'ACTIVE'
        - reasoning: clear explanation
        - confidence: 0.0 to 1.0
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            import json
            content = json.loads(response.choices[0].message.content)
            
            recommendation = LLMRecommendation(
                decision=content.get("decision", "ACTIVE"),
                reasoning=content.get("reasoning", "No reasoning provided"),
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
