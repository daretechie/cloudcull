import sys
from unittest.mock import MagicMock, patch
from src.adapters.gcp import GCPAdapter

@patch("src.adapters.gcp.compute_v1.InstancesClient")
@patch("src.adapters.gcp.monitoring_v3.MetricServiceClient")
def test_gcp_scan_with_mocks(mock_monitor_class, mock_compute_class):
    # Setup mocks
    mock_compute = mock_compute_class.return_value
    mock_monitor = mock_monitor_class.return_value
    
    # Mock logging client via sys.modules for global import interception
    mock_logging_mod = MagicMock()
    with patch.dict("sys.modules", {"google.cloud.logging_v2": mock_logging_mod}):
         # Configure the class on the module mock
         mock_logging_class = mock_logging_mod.LoggingServiceV2Client
         mock_logging = mock_logging_class.return_value
         
         adapter = GCPAdapter(project_id="test-project")
    
    # Mock Aggregated List
    mock_inst = MagicMock()
    mock_inst.name = "gcp-gpu-99"
    mock_inst.machine_type = "zones/us-central1-a/machineTypes/a2-highgpu-1g"
    mock_inst.status = "RUNNING"
    mock_inst.id = 123456789
    mock_inst.guest_accelerators = True
    
    mock_response = MagicMock()
    mock_response.instances = [mock_inst]
    mock_compute.aggregated_list.return_value = [("zones/us-central1-a", mock_response)]
    
    # Mock Metrics
    mock_point = MagicMock()
    mock_point.value.double_value = 0.05
    mock_ts = MagicMock()
    mock_ts.points = [mock_point]
    mock_monitor.list_time_series.return_value = [mock_ts]
    
    targets = adapter.scan()
    
    assert len(targets) == 1
    assert targets[0]['id'] == "gcp-gpu-99"
    assert targets[0]['metrics']['max_cpu'] == 5.0

@patch("src.adapters.gcp.compute_v1.InstancesClient")
def test_gcp_auth_error(mock_compute_class):
    # Test initialization failure
    mock_compute_class.side_effect = Exception("Auth Failed")
    
    adapter = GCPAdapter(project_id="test-project")
    assert adapter.simulated is True
