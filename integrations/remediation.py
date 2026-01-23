import logging
from typing import List, Dict, Any

logger = logging.getLogger("CloudCull.Remediation")

class TerraformRemediator:
    """
    IaC Evolution: Instead of raw deletions, generates a Terraform plan or state manipulation.
    """
    def generate_plan(self, zombied_instances: List[Dict]) -> Dict:
        logger.info("Generating 'Investor-Grade' IaC Remediation Plan...")
        
        plan = {
            "version": "1.0",
            "action": "decommission",
            "timestamp": logging.Formatter("%(asctime)s").format(logging.makeLogRecord({})),
            "resources": []
        }
        
        for z in zombied_instances:
            platform = z["platform"].upper()
            resource_id = z["id"]
            
            # Dynamic IaC Generation Logic
            if platform == "AWS":
                action = f"terraform state rm aws_instance.{resource_id}"
            elif platform == "AZURE":
                action = f"terraform state rm azurerm_linux_virtual_machine.{resource_id}"
            elif platform == "GCP":
                action = f"terraform state rm google_compute_instance.{resource_id}"
            else:
                action = f"terraform state rm cloud_resource.{resource_id}"

            plan["resources"].append({
                "id": resource_id,
                "platform": platform,
                "type": z["type"],
                "owner": z.get("owner", "Unknown"),
                "savings_potential": f"${z['rate'] * 24 * 30:,.2f}/mo",
                "remediation_type": "GitOps / State Management",
                "suggested_iac_action": action
            })
            
        return plan

    def generate_remediation_bundle(self, plan: Dict, output_path: str = "remediation.sh"):
        """Generates an executable shell script for rapid manual culling."""
        logger.info("Generating Executable Remediation Bundle: %s", output_path)
        
        with open(output_path, "w", encoding='utf-8') as f:
            f.write("#!/bin/bash\n")
            f.write("# CloudCull: Autonomous Remediation Bundle\n")
            f.write(f"# Generated at: {plan['timestamp']}\n\n")
            f.write("echo '⚠️  CRITICAL: Starting CloudCull ActiveOps Remediation...'\n\n")
            
            for r in plan['resources']:
                f.write(f"echo 'Sniping {r['platform']} {r['id']} ({r['owner']})...'\n")
                f.write(f"{r['suggested_iac_action']}\n")
            
            f.write("\necho '✅ Remediation Complete. Infrastructure hardened.'\n")
        
        import os
        os.chmod(output_path, 0o755)
        return output_path

    def save_manifest(self, plan: Dict, output_path: str = "remediation_manifest.json"):
        """Saves a structured manifest for CI/CD consumption."""
        import json
        with open(output_path, "w", encoding='utf-8') as f:
            json.dump(plan, f, indent=2)
        logger.info("Remediation Manifest saved to %s", output_path)
        return output_path

def execute_local_cull(adapter: Any, instance_id: str):
    """Direct execution wrapper."""
    adapter.stop_instance(instance_id)
