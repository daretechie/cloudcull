import requests
import logging
from functools import lru_cache

logger = logging.getLogger("CloudCull.Pricing")

class CloudPricing:
    """Industrial ROI Engine with real-time API integrations."""
    def __init__(self):
        # 2026 Core Baseline Rates (Fallback)
        self.rates = {
            "aws": {"p5.48xlarge": 98.32, "p4d.24xlarge": 32.77, "g5.48xlarge": 16.28, "g4dn.xlarge": 0.526},
            "gcp": {"a3-highgpu-8g": 31.02, "a2-highgpu-1g": 3.67, "g2-standard-8": 0.84},
            "azure": {"ND96isr_H100_v5": 33.15, "NC24ads_A100_v4": 3.40, "NC6s_v3": 0.90}
        }

    @lru_cache(maxsize=128)
    def _get_azure_retail_price(self, arm_type: str) -> float:
        """
        Fetches the current hourly retail price using the Azure Retail Prices API.
        Enhanced with tenacity retries for stability.
        """
        from tenacity import retry, stop_after_attempt, wait_exponential
        
        @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
        def fetch():
            # Note: Using 'Standard' for NC/NV series as a robust default
            query_filter = f"armSkuName eq '{arm_type}' and priceType eq 'Consumption' and serviceName eq 'Virtual Machines'"
            url = f"https://prices.azure.com/api/retail/prices?$filter={query_filter}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('Items'):
                # Azure API may return multiple regions; we take the first available
                return data['Items'][0].get('retailPrice', 0.0)
            return 0.0

        try:
            return fetch()
        except Exception as e:
            logger.warning("Azure Pricing API lookup failed for %s after retries: %s", arm_type, e)
        return 0.0

    def get_hourly_rate(self, platform: str, instance_type: str) -> float:
        platform_lower = platform.lower()
        if platform_lower == "azure":
            api_price = self._get_azure_retail_price(instance_type)
            if api_price > 0:
                return api_price

        # Fallback to local intelligence
        platform_rates = self.rates.get(platform_lower, {})
        instance_type_lower = instance_type.lower()
        for itype, rate in platform_rates.items():
            if itype.lower() in instance_type_lower:
                return rate
        
        # SAFETY CRITICAL: No implicit defaults for financial data.
        # If we don't know the price, we cannot safely automate a decision based on ROI.
        return None
