import boto3
import datetime
import logging
from typing import List, Dict, Any

from .base import AbstractAdapter

logger = logging.getLogger("CloudCull.AWS")

class AWSAdapter(AbstractAdapter):
    def __init__(self, region: str = "us-east-1", simulated: bool = False):
        self.region = region
        self.simulated = simulated
        self.gpu_types = ["p3", "p4", "g4", "g5", "p5"]
        
        if not self.simulated:
            try:
                from botocore.exceptions import ClientError, NoCredentialsError
                self.ec2 = boto3.client("ec2", region_name=region)
                self.cw = boto3.client("cloudwatch", region_name=region)
                self.cloudtrail = boto3.client("cloudtrail", region_name=region)
            except (NoCredentialsError, ClientError) as e:
                logger.error("AWS Authentication/Connection Failed: %s.", e)
                # No silent fallback to simulated=True here. 
                # Let verify_connection() or preflight check handle the failure.
                # However, we must ensure clients don't crash, so we just log and stay un-initialized.
                self.ec2 = None
                self.cw = None
                self.cloudtrail = None

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
            except Exception as e:
                logger.error("Error fetching AWS metric %s for %s: %s", metric_name, instance_id, e)
                return 0.0

        return {
            "max_cpu": get_stat('CPUUtilization'),
            "network_in": get_stat('NetworkIn', 'Average') / (1024 * 1024) # MBs
        }

    def get_attribution(self, instance_id: str, metadata: Dict = None) -> str:
        """
        Governance Layer: Uses a Tags-First strategy for attribution.
        1. Check tags (Owner, CreatedBy) - 0ms latency
        2. Fallback to CloudTrail - High latency
        """
        # 1. Tags-First Optimization
        if metadata and 'Tags' in metadata:
            tags = {t['Key'].lower(): t['Value'] for t in metadata['Tags']}
            for key in ['owner', 'createdby', 'creator', 'user']:
                if key in tags:
                    return tags[key]

        # 2. CloudTrail Fallback
        try:
            logger.info("Looking up attribution for %s via CloudTrail...", instance_id)
            paginator = self.cloudtrail.get_paginator('lookup_events')
            page_iterator = paginator.paginate(
                LookupAttributes=[{
                    'AttributeKey': 'ResourceName',
                    'AttributeValue': instance_id
                }],
                PaginationConfig={'MaxItems': 50, 'PageSize': 50}
            )

            for page in page_iterator:
                for event in page.get('Events', []):
                    # We look for RunInstances or CreateInstances (GPU context)
                    if event.get('EventName') in ['RunInstances', 'CreateInstances']:
                        return event.get('Username', 'Unknown')
                        
        except Exception as e:
            logger.warning("CloudTrail lookup failed for %s: %s", instance_id, e)
        return "Unknown"

    def _get_batch_metrics(self, instance_ids: List[str]) -> Dict[str, Dict[str, float]]:
        """
        High-Performance Batch Retrieval using CloudWatch GetMetricData.
        Retrieves CPU and Network metrics for up to 100 instances in a single API call (200 metrics).
        """
        if not instance_ids:
            return {}

        results = {iid: {"max_cpu": 0.0, "network_in": 0.0} for iid in instance_ids}
        
        # CloudWatch Constraints: Max 500 metrics per call. We fetch 2 per instance.
        # Safe batch size = 200 instances (400 metrics) to be safe.
        BATCH_SIZE = 200
        
        end_time = datetime.datetime.now(datetime.UTC)
        start_time = end_time - datetime.timedelta(hours=1)
        
        # Align to hour for cache hit optimization (Best Practice)
        start_time = start_time.replace(minute=0, second=0, microsecond=0)

        for i in range(0, len(instance_ids), BATCH_SIZE):
            batch_ids = instance_ids[i:i + BATCH_SIZE]
            metric_queries = []
            
            for index, iid in enumerate(batch_ids):
                # Query 1: CPU
                metric_queries.append({
                    'Id': f'cpu_{index}',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/EC2',
                            'MetricName': 'CPUUtilization',
                            'Dimensions': [{'Name': 'InstanceId', 'Value': iid}]
                        },
                        'Period': 3600,
                        'Stat': 'Maximum',
                    },
                    'ReturnData': True
                })
                # Query 2: NetworkIn
                metric_queries.append({
                    'Id': f'net_{index}',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/EC2',
                            'MetricName': 'NetworkIn',
                            'Dimensions': [{'Name': 'InstanceId', 'Value': iid}]
                        },
                        'Period': 3600,
                        'Stat': 'Average',
                    },
                    'ReturnData': True
                })

            try:
                # API Call: GetMetricData (Batch)
                response = self.cw.get_metric_data(
                    MetricDataQueries=metric_queries,
                    StartTime=start_time,
                    EndTime=end_time,
                    ScanBy='TimestampDescending'
                )
                
                # Map results back
                for res in response.get('MetricDataResults', []):
                    query_id = res['Id']
                    values = res.get('Values', [])
                    val = values[0] if values else 0.0
                    
                    # Parse ID: cpu_0 -> index 0
                    parts = query_id.split('_')
                    m_type = parts[0]
                    idx = int(parts[1])
                    target_iid = batch_ids[idx]
                    
                    if m_type == "cpu":
                        results[target_iid]["max_cpu"] = val
                    elif m_type == "net":
                        results[target_iid]["network_in"] = val / (1024 * 1024) # MBs

            except Exception as e:
                logger.error("Batch Metric Fetch Failed: %s", e)
                
        return results

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
        
        gpu_instances = []
        for res in response['Reservations']:
            for inst in res['Instances']:
                itype = inst['InstanceType']
                if any(gt in itype for gt in self.gpu_types):
                    gpu_instances.append(inst)

        if not gpu_instances:
            return []

        logger.info(f"Optimization: Batch analyzing {len(gpu_instances)} GPU instances...")
        
        # 1. Batch Metrics (API Optimization)
        # Replaces N calls with ~1 call
        all_ids = [inst['InstanceId'] for inst in gpu_instances]
        metrics_map = self._get_batch_metrics(all_ids)
        
        # 2. Parallel Attribution (IO Optimization)
        # Uses threads for CloudTrail lookups since they are IO-bound and independent
        from concurrent.futures import ThreadPoolExecutor
        
        targets = []
        
        def process_instance(inst):
            iid = inst['InstanceId']
            # Safe get from batch map
            metrics = metrics_map.get(iid, {"max_cpu": 0.0, "network_in": 0.0})
            
            # This is the slow part, running in thread
            # Optimization: Tag-level metadata passed for zero-latency attribution
            owner = self.get_attribution(iid, inst)
            
            return {
                "platform": "AWS",
                "id": iid,
                "type": inst['InstanceType'],
                "metrics": metrics,
                "owner": owner,
                "metadata": inst
            }

        with ThreadPoolExecutor(max_workers=20) as executor:
            targets = list(executor.map(process_instance, gpu_instances))
            
        return targets

    def stop_instance(self, instance_id: str, metadata: Dict[str, Any] = None):
        """Executes the kill-switch."""
        logger.warning("Executing Kill-Switch on AWS instance %s...", instance_id)
        if self.simulated:
            logger.info("[SIMULATED] Stopped AWS instance %s", instance_id)
            return
        self.ec2.stop_instances(InstanceIds=[instance_id])

    def verify_connection(self) -> bool:
        """Actively validates AWS credentials via STS."""
        if self.simulated:
            return True
        try:
            sts = boto3.client("sts", region_name=self.region)
            sts.get_caller_identity()
            return True
        except Exception as e:
            logger.error("AWS connection verification failed: %s", e)
            return False
