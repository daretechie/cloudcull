import logging
from typing import Dict, Any
from llm.base import BaseLLM, LLMResponse, LLMRecommendation

logger = logging.getLogger("CloudCull.LLM.Mock")

class MockProvider(BaseLLM):
    """
    High-fidelity Mock Provider for demonstrations and testing.
    Uses deterministic logic to simulate AI analysis.
    """
    def __init__(self, model: str = "mock-gpt-2026"):
        self.model = model

    def classify_instance(self, metadata: Dict[str, Any], metrics: Dict[str, Any]) -> LLMResponse:
        logger.info("[MOCK AI] Analyzing instance %s...", metadata.get('id', 'unknown'))
        
        cpu = metrics.get('max_cpu', 0.0)
        decision = "ZOMBIE" if cpu < 5.0 else "ACTIVE"
        
        reasoning = (
            f"Mock Analysis: The instance shows extremely low utilization ({cpu}% CPU). "
            f"Based on historical patterns, this instance is likely idle waste."
        ) if decision == "ZOMBIE" else (
            f"Mock Analysis: Instance is healthy and active ({cpu}% CPU)."
        )

        recommendation = LLMRecommendation(
            decision=decision,
            reasoning=reasoning,
            confidence=0.99 if decision == "ZOMBIE" else 0.95
        )
        
        return LLMResponse(
            raw_response="Simulated high-fidelity AI success.",
            recommendation=recommendation,
            usage={"prompt_tokens": 120, "completion_tokens": 45},
            model=self.model
        )
