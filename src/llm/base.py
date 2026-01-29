from abc import ABC, abstractmethod
from typing import Dict, Any
from pydantic import BaseModel, Field

class LLMRecommendation(BaseModel):
    decision: str = Field(description="ZOMBIE or ACTIVE")
    reasoning: str = Field(description="Clear explanation of why this decision was made")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score of the analysis")

class LLMResponse(BaseModel):
    raw_response: str
    recommendation: LLMRecommendation
    usage: Dict[str, int] = Field(default_factory=dict)
    model: str

class BaseLLM(ABC):
    """
    The Strategy Pattern Interface for Multi-Cloud Intelligence.
    Ensures all providers return a standardized LLMResponse object.
    """
    @abstractmethod
    def classify_instance(self, metadata: Dict[str, Any], metrics: Dict[str, Any]) -> LLMResponse:
        pass
