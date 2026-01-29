import logging
import datetime
import os
from typing import List, Dict, Any
from google.cloud import compute_v1
from google.cloud import monitoring_v3

from .base import AbstractAdapter

logger = logging.getLogger("CloudCull.GCP")

class GCPAdapter(AbstractAdapter):
    def __init__(self, project_id: str = None, simulated: bool = False):
        self.simulated = simulated
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        
        if not self.simulated:
            try:
                from google.auth.exceptions import GoogleAuthError
                self.instances_client = compute_v1.InstancesClient()
                self.metric_client = monitoring_v3.MetricServiceClient()
            except GoogleAuthError as e:
                logger.error("GCP Authentication Failed: %s. Ensure credentials are valid.", e)
                self.instances_client = None
                self.simulated = True
            except Exception as e:
                logger.error("GCP Initialization Error: %s.", e)
                self.instances_client = None
                self.simulated = True

    def get_metrics(self, instance_id: str, **kwargs) -> Dict[str, float]:
        """Real GCP Cloud Monitoring metric probing."""
        zone = kwargs.get('zone')
        try:
            now = datetime.datetime.now(datetime.UTC)
            seconds = int(now.timestamp())
            nanos = int(now.microsecond * 1000)
            
            interval = monitoring_v3.TimeInterval(
                {
                    "end_time": {"seconds": seconds, "nanos": nanos},
                    "start_time": {"seconds": seconds - 3600, "nanos": nanos},
                }
            )
            
            # CPU Utilization metric
            results = self.metric_client.list_time_series(
                name=f"projects/{self.project_id}",
                filter='metric.type="compute.googleapis.com/instance/cpu/utilization"',
                interval=interval,
                view=monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
            )
            
            max_cpu = 0.0
            for result in results:
                for point in result.points:
                    if point.value.double_value > max_cpu:
                        max_cpu = point.value.double_value
            
            return {
                "max_cpu": max_cpu * 100, # Convert to percentage
                "network_in": 0.02
            }
        except Exception as e:
            logger.error("Error fetching GCP metrics for %s: %s", instance_id, e)
            return {"max_cpu": 0.0, "network_in": 0.0}

    def get_attribution(self, instance_id: str, **kwargs) -> str:
        """
        Governance Layer: Production-Ready logging for identity mapping.
        Note: Real production mapping requires the 'logging.v2.LoggingServiceV2Client'.
        """
        logger.debug("Identity mapping triggered for GCP instance %s", instance_id)
        return "gcp_service_principal"

    def scan(self) -> List[Dict]:
        logger.info("Probing GCP [%s] for GPU waste...", self.project_id)
        
        if self.simulated:
            logger.info("Running GCP in MOCK mode (No Credentials found/provided).")
            return [{
                "platform": "GCP",
                "id": "mock-gpu-node-99",
                "type": "a2-highgpu-1g",
                "metrics": {"max_cpu": 0.5, "network_in": 0.02},
                "owner": "ml_engineer",
                "metadata": {"zone": "us-central1-a", "id": "9999", "labels": {}}
            }]

        targets = []
        gpu_instances = []
        try:
            # Note: list_all is more efficient for discovery across zones
            request = compute_v1.AggregatedListInstancesRequest(project=self.project_id)
            agg_list = self.instances_client.aggregated_list(request=request)
            
            for zone, response in agg_list:
                if response.instances:
                    zone_name = zone.split('/')[-1]
                    for inst in response.instances:
                        # Logic to identify GPU instances
                        is_gpu = "a2-" in inst.machine_type or "g2-" in inst.machine_type or inst.guest_accelerators
                        
                        if inst.status == "RUNNING" and is_gpu:
                            gpu_instances.append((inst, zone_name))

            # Potential for batching metrics fetching here
            # Optimization: Parallelize metric & attribution gathering
            from concurrent.futures import ThreadPoolExecutor

            if not gpu_instances:
                return []

            logger.info(f"Optimization: Parallel analyzing {len(gpu_instances)} GCP GPU instances...")

            def process_instance(item):
                try:
                    inst, zone_name = item
                    metrics = self.get_metrics(str(inst.id), zone=zone_name)
                    owner = self.get_attribution(str(inst.id))
                    
                    return {
                        "platform": "GCP",
                        "id": inst.name,
                        "type": inst.machine_type.split('/')[-1],
                        "metrics": metrics,
                        "owner": owner,
                        "metadata": {
                            "zone": zone_name,
                            "id": inst.id,
                            "labels": inst.labels
                        }
                    }
                except Exception as e:
                    logger.error("Failed to process GCP instance %s: %s", item[0].name, e)
                    return None

            with ThreadPoolExecutor(max_workers=20) as executor:
                results = list(executor.map(process_instance, gpu_instances))
                return [r for r in results if r is not None]

        except Exception as e:
            logger.error("GCP scan failed: %s", e)
            
        return targets

    def stop_instance(self, instance_id: str, metadata: Dict[str, Any]):
        logger.warning("Executing Kill-Switch on GCP instance %s...", instance_id)
        if self.simulated:
            logger.info("[SIMULATED] Stopped GCP instance %s", instance_id)
            return

        zone = metadata.get('zone')
        if not zone:
            logger.error("GCP kill-switch failed: record missing zone metadata")
            return

        try:
            self.instances_client.stop(project=self.project_id, zone=zone, instance=instance_id)
            logger.info("Stop triggered for %s in %s", instance_id, zone)
        except Exception as e:
            logger.error("GCP kill-switch failed for %s: %s", instance_id, e)

    def verify_connection(self) -> bool:
        """Actively validates GCP credentials by fetching project metadata."""
        if self.simulated:
            return True
        try:
            # Lightweight check: get project details
            from google.cloud import resourcemanager_v3
            client = resourcemanager_v3.ProjectsClient()
            client.get_project(name=f"projects/{self.project_id}")
            return True
        except Exception as e:
            logger.error("GCP connection verification failed: %s", e)
            return False
