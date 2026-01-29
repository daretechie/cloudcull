import pytest
from unittest.mock import MagicMock, patch
from src.main import CloudCullRunner, DiscoveryService

@pytest.fixture
def mock_context():
    with patch('src.adapters.AdapterRegistry.get_all_adapters') as mock_adapters, \
         patch('src.llm.factory.LLMFactory.get_provider') as mock_llm:
        
        # Setup Adapters
        aws_adapter = MagicMock()
        aws_adapter.__class__.__name__ = "AWSAdapter"
        
        azure_adapter = MagicMock()
        azure_adapter.__class__.__name__ = "AzureAdapter"
        
        mock_adapters.return_value = [aws_adapter, azure_adapter]
        
        # Setup LLM
        provider = MagicMock()
        mock_llm.return_value = provider
        
        yield {
            'aws': aws_adapter,
            'azure': azure_adapter,
            'brain': provider
        }

def test_execute_active_ops_calls_stop_before_terraform(mock_context):
    """
    CRITICAL TEST: Ensures that stop_instance is called on the cloud adapter
    BEFORE the remediator executes terraform state management.
    """
    ctx = mock_context
    aws = ctx['aws']
    
    # Setup call order tracker
    manager = MagicMock()
    manager.attach_mock(aws.stop_instance, 'stop_instance')
    
    # We need to mock the remediator correctly
    with patch('src.main.TerraformRemediator') as mock_remediator_class:
        mock_remediator = mock_remediator_class.return_value
        manager.attach_mock(mock_remediator.execute_remediation_plan, 'execute_remediation_plan')
        
        zombies = [{
            'id': 'i-123',
            'platform': 'AWS',
            'metadata': {'Name': 'Zombie-1'},
            'metrics': {}
        }]
        
        runner = CloudCullRunner(simulated=False, dry_run=False) # production mode
        runner.execute_active_ops(zombies)
        
        # Verify call sequence on the manager
        
        # This is a bit tricky with manager, let's just check the calls on the manager
        # Since we attached them, we can see the order.
        
        # Actually, let's use a simpler check:
        aws.stop_instance.assert_called_once_with('i-123', zombies[0]['metadata'])
        mock_remediator.execute_remediation_plan.assert_called_once()
        
        # To strictly verify order:
        stop_call_idx = -1
        exec_call_idx = -1
        
        for i, call in enumerate(manager.mock_calls):
            if call[0] == 'stop_instance':
                stop_call_idx = i
            if call[0] == 'execute_remediation_plan':
                exec_call_idx = i
                
        assert stop_call_idx != -1, "stop_instance was not called"
        assert exec_call_idx != -1, "execute_remediation_plan was not called"
        assert stop_call_idx < exec_call_idx, "stop_instance must be called BEFORE execute_remediation_plan"

def test_execute_active_ops_handles_adapter_not_found(mock_context):
    ctx = mock_context
    
    zombies = [{
        'id': 'v-999',
        'platform': 'NONEXISTENT',
        'metadata': {},
        'metrics': {}
    }]
    
    with patch('src.main.TerraformRemediator') as mock_remediator_class:
        mock_remediator = mock_remediator_class.return_value
        runner = CloudCullRunner(simulated=False, dry_run=False)
        
        runner.execute_active_ops(zombies)
        
        # Should not call stop or execute if no adapter found (unless failure allows)
        # In our implementation, if success_count == 0, it aborts.
        ctx['aws'].stop_instance.assert_not_called()
        mock_remediator.execute_remediation_plan.assert_not_called()
