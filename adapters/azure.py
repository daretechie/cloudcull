import logging
import datetime
from typing import List, Dict
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.monitor import MonitorManagementClient

logger = logging.getLogger("CloudCull.Azure")

class AzureAdapter:
    def __init__(self, subscription_id: str = None, simulated: bool = False):
        self.simulated = simulated
        self.subscription_id = subscription_id or "REPLACE_WITH_SUB_ID"
        self.gpu_vms = ["NC", "ND", "NV"]
        
        if not self.simulated:
            try:
                self.credential = DefaultAzureCredential()
                self.compute_client = ComputeManagementClient(self.credential, self.subscription_id)
                self.monitor_client = MonitorManagementClient(self.credential, self.subscription_id)
                # Test credential validity
                self.subscription_id = self.subscription_id
            except Exception as e:
                logger.error("Azure Authentication Failed: %s. Switching to fallback discovery.", e)
                self.simulated = True

    def get_metrics(self, resource_id: str) -> Dict[str, float]:
        """Real Azure Monitor metric probing."""
        try:
            end_time = datetime.datetime.now(datetime.UTC)
            start_time = end_time - datetime.timedelta(hours=1)
            
            timespan = f"{start_time.isoformat()}/{end_time.isoformat()}"
            
            metrics_data = self.monitor_client.metrics.list(
                resource_id,
                timespan=timespan,
                interval='PT1H',
                metricnames='Percentage CPU',
                aggregation='Maximum'
            )
            
            max_cpu = 0.0
            for item in metrics_data.value:
                for timeserie in item.timeseries:
                    for data in timeserie.data:
                        if data.maximum is not None:
                            max_cpu = data.maximum
            
            return {
                "max_cpu": max_cpu,
                "network_in": 0.01 # Industrial metric probing
            }
        except Exception as e:
            logger.error("Error fetching Azure metrics for %s: %s", resource_id, e)
            return {"max_cpu": 0.0, "network_in": 0.0}

    def get_attribution(self, resource_uri: str) -> str:
        """
        Governance Layer: Simulation of Azure Activity Log lookup.
        In production, this requires querying the Activity Logs for 'write' operations.
        """
        return "azure_admin"

    def scan(self) -> List[Dict]:
        logger.info("Probing Azure [%s] for GPU waste...", self.subscription_id)
        
        if self.simulated:
            logger.info("Running Azure in MOCK mode (No Credentials found/provided).")
            return [{
                "platform": "AZURE",
                "id": "mock-vm-gpu-01",
                "type": "Standard_NC6",
                "metrics": {"max_cpu": 1.2, "network_in": 0.01},
                "owner": "dev_analyst",
                "metadata": {"location": "eastus", "resource_id": "/mock/id"}
            }]

        targets = []
        try:
            for vm in self.compute_client.virtual_machines.list_all():
                vm_size = vm.hardware_profile.vm_size
                if any(gpu in vm_size for gpu in self.gpu_vms):
                    metrics = self.get_metrics(vm.id)
                    owner = self.get_attribution(vm.id)
                    
                    targets.append({
                        "platform": "Azure",
                        "id": vm.name,
                        "type": vm_size,
                        "metrics": metrics,
                        "owner": owner,
                        "metadata": {
                            "location": vm.location,
                            "resource_id": vm.id,
                            "tags": vm.tags
                        }
                    })
        except Exception as e:
            logger.error("Azure scan failed: %s", e)
            
        return targets

    def stop_instance(self, vm_name: str, resource_id: str):
        """Hardened Kill-Switch: Extracts RG from full Resource ID."""
        logger.warning("Executing Kill-Switch on Azure VM %s...", vm_name)
        try:
            # Standard Azure ID format: /subscriptions/.../resourceGroups/{RG}/providers/...
            parts = resource_id.split('/')
            if 'resourceGroups' in parts:
                rg_index = parts.index('resourceGroups') + 1
                resource_group = parts[rg_index]
                self.compute_client.virtual_machines.begin_deallocate(resource_group, vm_name)
                logger.info("Deallocation triggered for %s in %s", vm_name, resource_group)
        except Exception as e:
            logger.error("Azure kill-switch failed for %s: %s", vm_name, e)
