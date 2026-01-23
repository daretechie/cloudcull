import pytest
from unittest.mock import MagicMock, patch
from adapters.azure import AzureAdapter

@patch("adapters.azure.DefaultAzureCredential")
@patch("adapters.azure.ComputeManagementClient")
@patch("adapters.azure.MonitorManagementClient")
def test_azure_scan_with_mocks(mock_monitor_class, mock_compute_class, mock_cred_class):
    # Setup mocks
    mock_compute = mock_compute_class.return_value
    mock_monitor = mock_monitor_class.return_value
    
    adapter = AzureAdapter(subscription_id="test-sub")
    
    # Mock VM list
    mock_vm = MagicMock()
    mock_vm.name = "vm-gpu-01"
    mock_vm.hardware_profile.vm_size = "Standard_NC6"
    mock_vm.id = "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm-gpu-01"
    mock_vm.location = "eastus"
    mock_vm.tags = {"env": "prod"}
    
    mock_compute.virtual_machines.list_all.return_value = [mock_vm]
    
    # Mock Metrics
    mock_metric = MagicMock()
    mock_metric.maximum = 2.5
    mock_timeserie = MagicMock()
    mock_timeserie.data = [mock_metric]
    mock_item = MagicMock()
    mock_item.timeseries = [mock_timeserie]
    mock_monitor.metrics.list.return_value.value = [mock_item]
    
    targets = adapter.scan()
    
    assert len(targets) == 1
    assert targets[0]['id'] == "vm-gpu-01"
    assert targets[0]['metrics']['max_cpu'] == 2.5
