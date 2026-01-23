import pytest
from core.pricing import CloudPricing

def test_get_hourly_rate_aws_known():
    pricing = CloudPricing()
    # Test a known AWS instance type
    rate = pricing.get_hourly_rate("aws", "p4d.24xlarge")
    assert rate == 32.77

def test_get_hourly_rate_aws_unknown():
    pricing = CloudPricing()
    # Test an unknown AWS instance type returns default 1.5
    rate = pricing.get_hourly_rate("aws", "unknown.type")
    assert rate == 1.5

def test_get_hourly_rate_azure_fallback():
    pricing = CloudPricing()
    # Test Azure fallback rates
    rate = pricing.get_hourly_rate("azure", "NC24ads_A100_v4")
    assert rate == 3.40

def test_get_hourly_rate_ignore_case():
    pricing = CloudPricing()
    rate = pricing.get_hourly_rate("AWS", "P4D.24XLARGE")
    assert rate == 32.77
