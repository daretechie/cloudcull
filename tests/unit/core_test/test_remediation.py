from src.core.remediation import TerraformRemediator

def test_terraform_plan_generation():
    remediator = TerraformRemediator()
    zombies = [
        {
            "id": "i-123",
            "platform": "AWS",
            "type": "p4d.24xlarge",
            "owner": "dev_john",
            "rate": 32.77
        }
    ]
    plan = remediator.generate_plan(zombies)
    
    assert plan["version"] == "1.0"
    assert len(plan["resources"]) == 1
    assert plan["resources"][0]["id"] == "i-123"
    assert "terraform state rm" in plan["resources"][0]["suggested_iac_action"]
    assert "$23,594.40/mo" in plan["resources"][0]["savings_potential"] # 32.77 * 24 * 30
