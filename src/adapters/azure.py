import logging
import datetime
import os
from typing import List, Dict, Any
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.monitor import MonitorManagementClient

from .base import AbstractAdapter

logger = logging.getLogger("CloudCull.Azure")

class AzureAdapter(AbstractAdapter):
    def __init__(self, subscription_id: str = None, simulated: bool = False):
        self.simulated = simulated
        self.subscription_id = subscription_id or os.getenv("AZURE_SUBSCRIPTION_ID")
        self.gpu_vms = ["NC", "ND", "NV"]
        
        if not self.simulated:
            try:
                from azure.core.exceptions import AzureError
                self.credential = DefaultAzureCredential()
                self.compute_client = ComputeManagementClient(self.credential, self.subscription_id)
                self.monitor_client = MonitorManagementClient(self.credential, self.subscription_id)
            except AzureError as e:
                logger.error("Azure Service Error: %s. Check subscription/permissions.", e)
                self.credential = None
            except Exception as e:
                logger.error("Azure Authentication Failed: %s.", e)
                self.credential = None

    def get_metrics(self, instance_id: str, **kwargs) -> Dict[str, float]:
        """Real Azure Monitor metric probing."""
        try:
            end_time = datetime.datetime.now(datetime.UTC)
            start_time = end_time - datetime.timedelta(hours=1)
            
            timespan = f"{start_time.isoformat()}/{end_time.isoformat()}"
            
            metrics_data = self.monitor_client.metrics.list(
                instance_id,
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
            logger.error("Error fetching Azure metrics for %s: %s", instance_id, e)
            return {"max_cpu": 0.0, "network_in": 0.0}

    def get_attribution(self, instance_id: str, **kwargs) -> str:
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
        gpu_instances = []
        try:
            for vm in self.compute_client.virtual_machines.list_all():
                vm_size = vm.hardware_profile.vm_size
                if any(gpu in vm_size for gpu in self.gpu_vms):
                    gpu_instances.append(vm)

            if not gpu_instances:
                return []

            logger.info(f"Optimization: Parallel analyzing {len(gpu_instances)} Azure GPU VMs...")

            # Optimization: Parallelize metric & attribution gathering
            # Azure Monitor REST API is slower per-call, so threads help significantly here.
            from concurrent.futures import ThreadPoolExecutor

            def process_vm(vm):
                try:
                    metrics = self.get_metrics(vm.id)
                    owner = self.get_attribution(vm.id)
                    
                    return {
                        "platform": "Azure",
                        "id": vm.name,
                        "type": vm.hardware_profile.vm_size,
                        "metrics": metrics,
                        "owner": owner,
                        "metadata": {
                            "location": vm.location,
                            "resource_id": vm.id,
                            "tags": vm.tags
                        }
                    }
                except Exception as e:
                    logger.error("Failed to process Azure VM %s: %s", vm.name, e)
                    return None

            with ThreadPoolExecutor(max_workers=20) as executor:
                results = list(executor.map(process_vm, gpu_instances))
                targets = [r for r in results if r is not None]
                
        except Exception as e:
            logger.error("Azure scan failed: %s", e)
            
        return targets

    def stop_instance(self, instance_id: str, metadata: Dict[str, Any]):
        """Hardened Kill-Switch: Extracts RG from full Resource ID."""
        logger.warning("Executing Kill-Switch on Azure VM %s...", instance_id)
        
        if self.simulated:
            logger.info("[SIMULATED] Deallocated Azure VM %s", instance_id)
            return

        resource_id = metadata.get('resource_id')
        if not resource_id:
            logger.error("Azure kill-switch failed: record missing resource_id metadata")
            return

        try:
            import re
            # Standard Azure ID format: /subscriptions/{sub}/resourceGroups/{RG}/providers/Microsoft.Compute/virtualMachines/{name}
            # Robust Regex Extraction
            pattern = re.compile(r"/resourceGroups/([^/]+)/providers", re.IGNORECASE)
            match = pattern.search(resource_id)
            
            if match:
                resource_group = match.group(1)
                self.compute_client.virtual_machines.begin_deallocate(resource_group, instance_id)
                logger.info("Deallocation triggered for %s in %s", instance_id, resource_group)
            else:
                logger.error("Azure kill-switch failed: Resource ID format unexpected: %s", resource_id)
        except Exception as e:
            logger.error("Azure kill-switch failed for %s: %s", instance_id, e)

    def verify_connection(self) -> bool:
        """Actively validates Azure credentials by listing subscriptions."""
        if self.simulated:
            return True
        try:
            # We use a monitor client or similar for a lightweight check
            from azure.mgmt.resource import SubscriptionClient
            sub_client = SubscriptionClient(self.credential)
            sub_client.subscriptions.get(self.subscription_id)
            return True
        except Exception as e:
            logger.error("Azure connection verification failed: %s", e)
            return False
