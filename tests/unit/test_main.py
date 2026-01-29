import pytest
from unittest.mock import MagicMock, patch
from src.main import CloudCullRunner, DiscoveryService

@pytest.fixture
def mock_adapters():
    with patch('src.adapters.AdapterRegistry.get_all_adapters') as mock_all:
        aws = MagicMock()
        azure = MagicMock()
        gcp = MagicMock()
        mock_all.return_value = [aws, azure, gcp]
        yield aws, azure, gcp

@pytest.fixture
def mock_brain():
    with patch('src.llm.factory.LLMFactory.get_provider') as mock_llm:
        provider = MagicMock()
        mock_llm.return_value = provider
        yield provider

def test_discovery_service_scans_all_adapters(mock_adapters):
    aws, azure, gcp = mock_adapters
    aws.scan.return_value = [{'id': 'aws-1', 'platform': 'AWS'}]
    azure.scan.return_value = [{'id': 'az-1', 'platform': 'AZURE'}]
    gcp.scan.return_value = [{'id': 'gcp-1', 'platform': 'GCP'}]
    
    service = DiscoveryService(region="us-east-1", simulated=True)
    results = service.scan_all()
    
    assert len(results) == 3
    aws.scan.assert_called_once()
    azure.scan.assert_called_once()
    gcp.scan.assert_called_once()

def test_runner_audit_flow(mock_adapters, mock_brain):
    aws, _, _ = mock_adapters
    aws.scan.return_value = [{
        'id': 'i-123', 
        'platform': 'AWS', 
        'type': 'p3.2xlarge', 
        'metadata': {}, 
        'metrics': {},
        'owner': 'admin'
    }]
    
    # Mock LLM decision
    report = MagicMock()
    report.recommendation.decision = "ZOMBIE"
    report.recommendation.reasoning = "Idle GPU"
    mock_brain.classify_instance.return_value = report
    
    runner = CloudCullRunner(simulated=True, dry_run=True)
    results = runner.run_audit()
    
    assert len(results) == 1
    assert results[0]['status'] == "ZOMBIE"

def test_main_entrypoint_with_zombies(mock_adapters, mock_brain):
    from src.main import main
    import sys
    
    aws, _, _ = mock_adapters
    aws.scan.return_value = [{
        'id': 'i-123', 
        'platform': 'AWS', 
        'type': 'p3.2xlarge', 
        'metadata': {}, 
        'metrics': {'max_cpu': 5.0, 'network_in': 100.0}, 
        'owner': 'admin',
        'rate': 12.50,
        'status': 'ZOMBIE'
    }]
    
    # Mock sys.argv
    with patch.object(sys, 'argv', ['main.py', '--simulated', '--dry-run']):
        # Mock LLM decision for the entrypoint call
        report = MagicMock()
        report.recommendation.decision = "ZOMBIE"
        report.recommendation.reasoning = "Idle"
        mock_brain.classify_instance.return_value = report
        
        with patch('builtins.print'):
            main()
    
    aws.scan.assert_called()
