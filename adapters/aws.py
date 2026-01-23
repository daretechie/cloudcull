import boto3
import datetime
import logging
from typing import List, Dict

logger = logging.getLogger("CloudCull.AWS")

class AWSAdapter:
    def __init__(self, region: str = "us-east-1", simulated: bool = False):
        self.region = region
        self.simulated = simulated
        self.gpu_types = ["p3", "p4", "g4", "g5", "p5"]
        
        if not self.simulated:
            try:
                self.ec2 = boto3.client("ec2", region_name=region)
                self.cw = boto3.client("cloudwatch", region_name=region)
                self.cloudtrail = boto3.client("cloudtrail", region_name=region)
            except Exception as e:
                logger.error("AWS Authentication Failed: %s. Falling back to simulated mode.", e)
                self.simulated = True

    def get_metrics(self, instance_id: str, minutes: int = 60) -> Dict[str, float]:
        """Precision Metric Probing: CPU + NetworkIn."""
        end_time = datetime.datetime.now(datetime.UTC)
        start_time = end_time - datetime.timedelta(minutes=minutes)
        
        def get_stat(metric_name: str, stat: str = 'Maximum') -> float:
            try:
                res = self.cw.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName=metric_name,
                    Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,
                    Statistics=[stat]
                )
                pts = res.get('Datapoints', [])
                return pts[0][stat] if pts else 0.0
            except Exception:
                logger.error("Error fetching AWS metric %s", metric_name)
                return 0.0

        return {
            "max_cpu": get_stat('CPUUtilization'),
            "network_in": get_stat('NetworkIn', 'Average') / (1024 * 1024) # MBs
        }

    def get_attribution(self, instance_id: str) -> str:
        """
        Governance Layer: Uses CloudTrail to find who launched the instance.
        """
        try:
            logger.info("Looking up attribution for %s via CloudTrail...", instance_id)
            response = self.cloudtrail.lookup_events(
                LookupAttributes=[{
                    'AttributeKey': 'ResourceName',
                    'AttributeValue': instance_id
                }],
                MaxResults=10
            )
            for event in response.get('Events', []):
                if event.get('EventName') == 'RunInstances':
                    return event.get('Username', 'Unknown')
        except Exception:
            logger.warning("CloudTrail lookup failed for %s", instance_id)
        return "Unknown"

    def scan(self) -> List[Dict]:
        logger.info("Probing AWS [%s] for GPU waste...", self.region)
        
        if self.simulated:
            logger.info("Running AWS in MOCK mode (No Credentials found/provided).")
            return [{
                "platform": "AWS",
                "id": "i-0a1b2c3d4e5f6g7h8",
                "type": "p4d.24xlarge",
                "metrics": {"max_cpu": 0.2, "network_in": 0.05},
                "owner": "research_lead",
                "metadata": {"InstanceId": "i-0a1b2c3d4e5f6g7h8", "InstanceType": "p4d.24xlarge"}
            }]

        filters = [{'Name': 'instance-state-name', 'Values': ['running']}]
        response = self.ec2.describe_instances(Filters=filters)
        
        targets = []
        for res in response['Reservations']:
            for inst in res['Instances']:
                itype = inst['InstanceType']
                if any(gt in itype for gt in self.gpu_types):
                    instance_id = inst['InstanceId']
                    metrics = self.get_metrics(instance_id)
                    owner = self.get_attribution(instance_id)
                    
                    targets.append({
                        "platform": "AWS",
                        "id": instance_id,
                        "type": itype,
                        "metrics": metrics,
                        "owner": owner,
                        "metadata": inst
                    })
        return targets

    def stop_instance(self, instance_id: str):
        """Executes the kill-switch."""
        logger.warning("Executing Kill-Switch on AWS instance %s...", instance_id)
        self.ec2.stop_instances(InstanceIds=[instance_id])
