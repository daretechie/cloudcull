from unittest.mock import MagicMock, patch
from src.main import CloudCullRunner

def test_runner_graceful_degradation_on_adapter_failure():
    """
    Ensures that if one adapter fails initialization/verification, 
    the system logs the error and continues with the others (if possible).
    
    Currently, the system exits (sys.exit(1)). We want to verify it 
    eventually changes to a more resilient model.
    """
    with patch('src.adapters.AdapterRegistry.get_all_adapters') as mock_adapters, \
         patch('src.llm.factory.LLMFactory.get_provider') as mock_brain:
        
        # 1. Setup one success (AWS) and one failure (Azure)
        aws = MagicMock()
        aws.__class__.__name__ = "AWSAdapter"
        aws.verify_connection.return_value = True
        aws.scan.return_value = []
        
        azure = MagicMock()
        azure.__class__.__name__ = "AzureAdapter"
        azure.verify_connection.return_value = False # FAILURE
        
        mock_adapters.return_value = [aws, azure]
        mock_brain.return_value = MagicMock()
        
        runner = CloudCullRunner(simulated=False, dry_run=True)
        
        # Graceful Degradation Check: Should NOT exit if at least one works
        runner._preflight_check()
        
        # Verify AWS remains, Azure is removed
        assert len(runner.discovery.adapters) == 1
        assert type(runner.discovery.adapters[0]).__name__ == "AWSAdapter"

def test_runner_continues_if_at_least_one_adapter_works():
    """
    FUTURE GOAL: The system should not exit if at least one adapter is healthy.
    This test will be used to verify the resilience refactor.
    """
    with patch('src.adapters.AdapterRegistry.get_all_adapters') as mock_adapters, \
         patch('src.llm.factory.LLMFactory.get_provider') as mock_brain:
        
        # 2 adapters: 1 working, 1 broken
        good_adapter = MagicMock()
        good_adapter.verify_connection.return_value = True
        good_adapter.scan.return_value = [{'id': 'ok-1', 'platform': 'TEST', 'status': 'ACTIVE', 'metrics': {}, 'metadata': {}}]
        
        bad_adapter = MagicMock()
        bad_adapter.verify_connection.return_value = False
        
        mock_adapters.return_value = [good_adapter, bad_adapter]
        mock_brain.return_value.classify_instance.return_value.recommendation.decision = "ACTIVE"
        
        runner = CloudCullRunner(simulated=False, dry_run=True)
        # Should filter out the bad adapter but keep the good one
        assert len(runner.discovery.adapters) == 1
        
        results = runner.run_audit()
        assert len(results) == 1
        assert results[0]['id'] == 'ok-1'
