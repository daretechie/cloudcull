import logging
from typing import Dict, Any
from anthropic import Anthropic
from ..base import BaseLLM, LLMResponse, LLMRecommendation

logger = logging.getLogger("CloudCull.LLM.Anthropic")

class AnthropicProvider(BaseLLM):
    """
    Anthropic Implementation for Claude 3 series.
    """
    def __init__(self, api_key: str = None):
        from ...core.settings import settings
        api_key = api_key or settings.anthropic_api_key
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022" 

    def classify_instance(self, metadata: Dict[str, Any], metrics: Dict[str, Any]) -> LLMResponse:
        logger.info("Claude analyzing instance %s...", metadata.get('id', 'unknown'))
        
        system_prompt = """
        You are an expert Cloud FinOps Auditor. Your task is to classify a GPU instance as 'ZOMBIE' or 'ACTIVE'.
        - ZOMBIE: Low CPU (<5% max for 1hr), minimal network activity, and no clear signs of iterative work.
        - ACTIVE: Significant CPU spikes, consistent load, or vital service indicators.
        
        Return ONLY a JSON object with:
        {
          "decision": "ZOMBIE" | "ACTIVE",
          "reasoning": "step-by-step logic",
          "confidence": 0.0-1.0
        }
        """
        
        # Prompt Injection Protection: Sanitize metadata keys and values
        from ..utils import sanitize_for_prompt
        safe_metadata = sanitize_for_prompt(metadata)
        safe_metrics = sanitize_for_prompt(metrics)
        
        user_input = f"METADATA: {safe_metadata}\nMETRICS: {safe_metrics}"
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_input}]
        )
        
        # Robust JSON Extraction (Improved)
        from ..utils import extract_json_from_text
        text = response.content[0].text
        content = extract_json_from_text(text)
        
        if not content:
            logger.error("Failed to parse LLM response: JSON extraction empty | Text: %s", text[:100])
            content = {"decision": "ACTIVE", "reasoning": "Failed to parse structured response", "confidence": 0.0}


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
