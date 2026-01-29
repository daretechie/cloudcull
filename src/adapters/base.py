import abc
from typing import List, Dict, Any

class AbstractAdapter(abc.ABC):
    @abc.abstractmethod
    def scan(self) -> List[Dict[str, Any]]:
        """Scans the cloud environment for relevant targets."""
        pass

    @abc.abstractmethod
    def get_metrics(self, instance_id: str, **kwargs) -> Dict[str, float]:
        """Fetches telemetry for a specific instance."""
        pass

    @abc.abstractmethod
    def get_attribution(self, instance_id: str, **kwargs) -> str:
        """Finds the owner/launcher of the instance."""
        pass

    @abc.abstractmethod
    def stop_instance(self, instance_id: str, metadata: Dict[str, Any]):
        """Executes the termination/stop action."""
        pass

    @abc.abstractmethod
    def verify_connection(self) -> bool:
        """Actively validates cloud credentials/connectivity."""
        pass
