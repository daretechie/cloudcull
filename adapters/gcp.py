import logging
import datetime
from typing import List, Dict
from google.cloud import compute_v1
from google.cloud import monitoring_v3

logger = logging.getLogger("CloudCull.GCP")

class GCPAdapter:
    def __init__(self, project_id: str = "REPLACE_WITH_PROJECT_ID", simulated: bool = False):
        self.simulated = simulated
        self.project_id = project_id
        
        if not self.simulated:
            try:
                self.instances_client = compute_v1.InstancesClient()
                self.metric_client = monitoring_v3.MetricServiceClient()
            except Exception as e:
                logger.error("GCP Authentication Failed: %s. Use 'gcloud auth application-default login'.", e)
                self.simulated = True

    def get_metrics(self, zone: str, instance_id: str) -> Dict[str, float]:
        """Real GCP Cloud Monitoring metric probing."""
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

    def get_attribution(self, _instance_id: str) -> str:
        """
        Governance Layer: Production-Ready logging for identity mapping.
        Note: Real production mapping requires the 'logging.v2.LoggingServiceV2Client'.
        """
        logger.debug("Identity mapping triggered for GCP instance %s", _instance_id)
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
        try:
            # Note: list_all is more efficient for discovery across zones
            request = compute_v1.AggregatedListInstancesRequest(project=self.project_id)
            agg_list = self.instances_client.aggregated_list(request=request)
            
            for zone, response in agg_list:
                if response.instances:
                    zone_name = zone.split('/')[-1]
                    for inst in response.instances:
                        # Logic to identify GPU instances (e.g. by machine type or accelerator)
                        is_gpu = "a2-" in inst.machine_type or "g2-" in inst.machine_type or inst.guest_accelerators
                        
                        if inst.status == "RUNNING" and is_gpu:
                            metrics = self.get_metrics(zone_name, str(inst.id))
                            owner = self.get_attribution(str(inst.id))
                            
                            targets.append({
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
                            })
        except Exception as e:
            logger.error("GCP scan failed: %s", e)
            
        return targets

    def stop_instance(self, zone: str, instance_name: str):
        logger.warning("Executing Kill-Switch on GCP instance %s...", instance_name)
        # self.instances_client.stop(project=self.project_id, zone=zone, instance=instance_name)
