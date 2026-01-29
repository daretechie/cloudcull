from unittest.mock import MagicMock, patch
from src.llm.factory import LLMFactory

@patch("openai.OpenAI")
def test_openai_provider_mock(mock_client_class):
    # Mocking OpenAI Client and its methods
    mock_client = mock_client_class.return_value
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"decision": "ZOMBIE", "reasoning": "Idle", "confidence": 0.9}'
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_client.chat.completions.create.return_value = mock_response
    
    provider = LLMFactory.get_provider("openai")
    res = provider.classify_instance({"id": "test"}, {"max_cpu": 1.0})
    
    assert res.recommendation.decision == "ZOMBIE"
    assert res.model == "gpt-4o"

@patch("src.llm.providers.anthropic.Anthropic")
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test-123"})
def test_anthropic_provider_mock(mock_client_class):
    # Mocking Anthropic Client
    mock_client = mock_client_class.return_value
    mock_response = MagicMock()
    mock_response.content[0].text = '{"decision": "ZOMBIE", "reasoning": "Claude analysis", "confidence": 0.95}'
    mock_response.usage.input_tokens = 100
    mock_response.usage.output_tokens = 50
    mock_client.messages.create.return_value = mock_response
    
    provider = LLMFactory.get_provider("claude")
    res = provider.classify_instance({"id": "test"}, {"max_cpu": 1.0})
    
    assert res.recommendation.decision == "ZOMBIE"
    assert "Claude" in res.recommendation.reasoning

@patch("google.genai.Client")
def test_google_provider_mock(mock_client_class):
    # Mocking Google Client
    mock_client = mock_client_class.return_value
    mock_response = MagicMock()
    mock_response.text = '{"decision": "ZOMBIE", "reasoning": "Gemini analysis", "confidence": 0.92}'
    mock_response.usage_metadata.prompt_token_count = 100
    mock_response.usage_metadata.candidates_token_count = 50
    mock_client.models.generate_content.return_value = mock_response
    
    provider = LLMFactory.get_provider("gemini")
    res = provider.classify_instance({"id": "test"}, {"max_cpu": 1.0})
    
    assert res.recommendation.decision == "ZOMBIE"
    assert "Gemini" in res.recommendation.reasoning

@patch("groq.Groq")
def test_groq_provider_mock(mock_client_class):
    # Mocking Groq Client
    mock_client = mock_client_class.return_value
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"decision": "ZOMBIE", "reasoning": "Groq analysis", "confidence": 0.9}'
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_client.chat.completions.create.return_value = mock_response
    
    provider = LLMFactory.get_provider("llama")
    res = provider.classify_instance({"id": "test"}, {"max_cpu": 1.0})
    
    assert res.recommendation.decision == "ZOMBIE"
    assert "Groq" in res.recommendation.reasoning
