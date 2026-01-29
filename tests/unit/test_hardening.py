import pytest
from src.main import scrub_metadata

def test_scrub_metadata_basic():
    """Verify that sensitive keys are scrubbed from tags."""
    metadata = {
        "id": "i-123",
        "tags": {
            "Name": "prod-gpu",
            "db_password": "super-secret-pass",
            "cloud_token": "abc-123-token"
        }
    }
    
    scrubbed = scrub_metadata(metadata)
    
    assert scrubbed["tags"]["Name"] == "prod-gpu"
    assert scrubbed["tags"]["db_password"] == "***SCRUBBED***"
    assert scrubbed["tags"]["cloud_token"] == "***SCRUBBED***"

def test_scrub_metadata_gcp_labels():
    """Verify that GCP labels are also scrubbed."""
    metadata = {
        "labels": {
            "env": "prod",
            "api_key": "secret-key-01"
        }
    }
    
    scrubbed = scrub_metadata(metadata)
    
    assert scrubbed["labels"]["env"] == "prod"
    assert scrubbed["labels"]["api_key"] == "***SCRUBBED***"

def test_scrub_metadata_recursive():
    """Verify that sensitive keys are scrubbed from deep-nested objects."""
    metadata = {
        "id": "i-123",
        "nested_data": {
            "sub_section": {
                "user_token": "hidden-payload",
                "display_name": "visible"
            },
            "credentials": [
                {"password": "pass1"},
                {"type": "public"}
            ]
        }
    }
    
    scrubbed = scrub_metadata(metadata)
    
    # Check nesting
    assert scrubbed["nested_data"]["sub_section"]["user_token"] == "***SCRUBBED***"
    assert scrubbed["nested_data"]["sub_section"]["display_name"] == "visible"
    
    # 'credentials' contains 'credential', so the whole list is scrubbed
    assert scrubbed["nested_data"]["credentials"] == "***SCRUBBED***"

def test_scrub_metadata_empty_or_none():
    """Verify robustness with empty or missing metadata."""
    assert scrub_metadata(None) == {}
    assert scrub_metadata({}) == {}
    
    metadata_no_tags = {"id": "i-1"}
    assert scrub_metadata(metadata_no_tags) == {"id": "i-1"}
