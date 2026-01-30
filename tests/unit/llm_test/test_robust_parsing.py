from src.llm.providers.anthropic import AnthropicProvider
from unittest.mock import MagicMock

def test_robust_json_extraction_markdown():
    """Verifies that the provider can extract JSON from markdown blocks."""
    provider = AnthropicProvider(api_key="sk-test-123")
    
    # Simulate a "chatty" response with markdown
    dirty_response = """
    I have analyzed the instance. Here is the decision in JSON format:
    ```json
    {
        "decision": "ZOMBIE",
        "reasoning": "CPU is too low",
        "confidence": 0.99
    }
    ```
    Please let me know if you need more info.
    """
    
    mock_client = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=dirty_response)]
    mock_msg.usage.input_tokens = 10
    mock_msg.usage.output_tokens = 20
    mock_client.messages.create.return_value = mock_msg
    provider.client = mock_client
    
    report = provider.classify_instance({"id": "i-123"}, {"max_cpu": 0.5})
    assert report.recommendation.decision == "ZOMBIE"
    assert "CPU is too low" in report.recommendation.reasoning

def test_robust_json_extraction_malformed():
    """Verifies fallback when JSON is completely missing."""
    provider = AnthropicProvider(api_key="sk-test-123")
    
    malformed_response = "The instance looks fine to me, I won't give you JSON."
    
    mock_client = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=malformed_response)]
    mock_msg.usage.input_tokens = 10
    mock_msg.usage.output_tokens = 20
    mock_client.messages.create.return_value = mock_msg
    provider.client = mock_client
    
    report = provider.classify_instance({"id": "i-123"}, {"max_cpu": 0.5})
    # Should fallback to ACTIVE per implementation logic in handle_parsing_error (implied by default)
    assert report.recommendation.decision == "ACTIVE"
    assert "Failed to parse structured response" in report.recommendation.reasoning
