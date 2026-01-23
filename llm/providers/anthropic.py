import os
import logging
from typing import Dict, Any
from anthropic import Anthropic
from llm.base import BaseLLM, LLMResponse, LLMRecommendation

logger = logging.getLogger("CloudCull.LLM.Anthropic")

class AnthropicProvider(BaseLLM):
    """
    Anthropic Implementation for Claude 3 series.
    """
    def __init__(self, api_key: str = None):
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022" 

    def classify_instance(self, metadata: Dict[str, Any], metrics: Dict[str, Any]) -> LLMResponse:
        logger.info("Claude analyzing instance %s...", metadata.get('id', 'unknown'))
        
        prompt = f"Target Instance: {metadata}\nMetrics: {metrics}\nAnalyze and decide ZOMBIE or ACTIVE. Return JSON."
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Industrial JSON Extraction (Regex-safe heuristic)
        import json
        import re
        text = response.content[0].text
        try:
            # Look for the last curly-brace delimited block in the response
            match = re.search(r'\{.*\}', text, re.DOTALL)
            content = json.loads(match.group(0)) if match else {}
        except Exception:
            content = {"decision": "ACTIVE", "reasoning": "Extraction failure", "confidence": 0.0}

        recommendation = LLMRecommendation(
            decision=content.get("decision", "ACTIVE"),
            reasoning=content.get("reasoning", text[:500]),
            confidence=content.get("confidence", 0.5)
        )
        
        return LLMResponse(
            raw_response=text,
            recommendation=recommendation,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            },
            model=self.model
        )
