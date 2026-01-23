import pytest
from unittest.mock import MagicMock, patch
from adapters.aws import AWSAdapter

@pytest.fixture
def mock_boto3_clients():
    with patch('boto3.client') as mock_client:
        ec2 = MagicMock()
        cw = MagicMock()
        ct = MagicMock()
        
        def side_effect(service, **kwargs):
            if service == 'ec2': return ec2
            if service == 'cloudwatch': return cw
            if service == 'cloudtrail': return ct
            return MagicMock()
            
        mock_client.side_effect = side_effect
        yield ec2, cw, ct

def test_aws_scan_finds_gpu_instances(mock_boto3_clients):
    ec2, cw, ct = mock_boto3_clients
    
    # Mock EC2 describe_instances
    ec2.describe_instances.return_value = {
        'Reservations': [{
            'Instances': [
                {
                    'InstanceId': 'i-gpu-123',
                    'InstanceType': 'g4dn.xlarge',
                    'State': {'Name': 'running'}
                },
                {
                    'InstanceId': 'i-cpu-456',
                    'InstanceType': 't3.micro',
                    'State': {'Name': 'running'}
                }
            ]
        }]
    }
    
    # Mock CloudWatch metrics
    cw.get_metric_statistics.return_value = {
        'Datapoints': [{'Maximum': 0.5}]
    }
    
    # Mock CloudTrail attribution
    ct.lookup_events.return_value = {
        'Events': [{'EventName': 'RunInstances', 'Username': 'test_user'}]
    }
    
    adapter = AWSAdapter(region="us-east-1")
    targets = adapter.scan()
    
    # Should only find the GPU instance
    assert len(targets) == 1
    assert targets[0]['id'] == 'i-gpu-123'
    assert targets[0]['owner'] == 'test_user'
    assert targets[0]['metrics']['max_cpu'] == 0.5

def test_aws_stop_instance(mock_boto3_clients):
    ec2, _, _ = mock_boto3_clients
    adapter = AWSAdapter()
    adapter.stop_instance("i-123")
    ec2.stop_instances.assert_called_once_with(InstanceIds=["i-123"])
