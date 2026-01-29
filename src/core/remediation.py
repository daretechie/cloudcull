import logging
import datetime
from typing import List, Dict

logger = logging.getLogger("CloudCull.Remediation")

class TerraformRemediator:
    """
    IaC Evolution: Instead of raw deletions, generates a Terraform plan or state manipulation.
    """
    
    RESOURCE_MAPPING = {
        "AWS": "aws_instance",
        "AZURE": "azurerm_linux_virtual_machine",
        "GCP": "google_compute_instance"
    }

    def generate_plan(self, zombied_instances: List[Dict]) -> Dict:
        logger.info("Generating 'Investor-Grade' IaC Remediation Plan...")
        
        timestamp = datetime.datetime.now(datetime.UTC).isoformat()
        
        plan = {
            "version": "1.0",
            "action": "decommission",
            "timestamp": timestamp,
            "resources": []
        }
        
        # Lazy import to avoid top-level dependency
        import shlex

        for z in zombied_instances:
            platform = z["platform"].upper()
            resource_id = shlex.quote(z["id"])
            
            # Dynamic IaC Generation Logic
            resource_type = self.RESOURCE_MAPPING.get(platform, "cloud_resource")
            action = f"terraform state rm {resource_type}.{resource_id}"

            plan["resources"].append({
                "id": z["id"],
                "platform": platform,
                "type": z["type"],
                "owner": z.get("owner", "Unknown"),
                "savings_potential": f"${z['rate'] * 24 * 30:,.2f}/mo",
                "remediation_type": "GitOps / State Management",
                "suggested_iac_action": action
            })
            
        return plan

    def execute_remediation_plan(self, plan: Dict):
        """
        Executes the remediation plan directly using secure subprocess calls.
        No intermediate shell scripts are generated to prevent injection attacks.
        """
        import subprocess
        import re

        logger.info("🛡️ Executing ActiveOps Remediation via Secure Subprocess...")
        
        # Validation Pattern for Instance IDs (Alphanumeric + dashes only)
        # Prevents any weird characters from slipping into the command even with shell=False
        SAFE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9\-]+$")

        success_count = 0
        fail_count = 0

        for r in plan['resources']:
            resource_id = r['id']
            platform = r['platform'].upper()
            
            # 1. Strict Input Validation
            if not SAFE_ID_PATTERN.match(resource_id):
                logger.error(f"❌ SECURITY ALERT: Invalid Resource ID '{resource_id}' detected. Skipping.")
                fail_count += 1
                continue

            # 2. Construct Command as List (No Shell Interpolation)
            resource_type = self.RESOURCE_MAPPING.get(platform)
            if not resource_type:
                logger.warning(f"Unknown platform {platform} for resource {resource_id}. Skipping.")
                fail_count += 1
                continue

            # Target: terraform state rm aws_instance.i-12345
            target_address = f"{resource_type}.{resource_id}"
            cmd = ["terraform", "state", "rm", target_address]

            try:
                logger.info(f"⚡ Sniping {target_address}...")
                # shell=False is default, but explicit is better than implicit security
                subprocess.run(cmd, check=True, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                success_count += 1
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Terraform Execution Failed for {resource_id}: {e.stderr.decode().strip()}")
                fail_count += 1
            except FileNotFoundError:
                logger.critical("❌ Terraform binary not found! Ensuring 'terraform' is in PATH.")
                return

        logger.info(f"✅ ActiveOps Complete. Success: {success_count}, Failed: {fail_count}")

    def check_terraform_binary(self) -> bool:
        """Active validation of the environment for the Service Provider tool."""
        import shutil
        return shutil.which("terraform") is not None

    def save_manifest(self, plan: Dict, output_path: str = "config/remediation_manifest.json"):
        """Saves a structured manifest for CI/CD consumption."""
        import json
        with open(output_path, "w", encoding='utf-8') as f:
            json.dump(plan, f, indent=2)
        logger.info("Remediation Manifest saved to %s", output_path)
        return output_path
