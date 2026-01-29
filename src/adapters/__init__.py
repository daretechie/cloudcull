from typing import List
from .base import AbstractAdapter
from .aws import AWSAdapter
from .azure import AzureAdapter
from .gcp import GCPAdapter

class AdapterRegistry:
    @staticmethod
    def get_all_adapters(region: str = "us-east-1", simulated: bool = False) -> List[AbstractAdapter]:
        return [
            AWSAdapter(region=region, simulated=simulated),
            AzureAdapter(simulated=simulated),
            GCPAdapter(simulated=simulated)
        ]

    @staticmethod
    def get_adapter_by_platform(platform: str, region: str = "us-east-1", simulated: bool = False) -> AbstractAdapter:
        platform = platform.upper()
        if platform == "AWS":
            return AWSAdapter(region=region, simulated=simulated)
        elif platform == "AZURE":
            return AzureAdapter(simulated=simulated)
        elif platform == "GCP":
            return GCPAdapter(simulated=simulated)
        raise ValueError(f"Unsupported platform: {platform}")
