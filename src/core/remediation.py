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

    def _find_resource_in_state(self, resource_type: str, physical_id: str) -> str:
        """
        Smart Lookup: Scans Terraform state to find the logical address (e.g. 'aws_instance.worker')
        that corresponds to the physical ID (e.g. 'i-12345').
        """
        import subprocess  # nosec
        import json
        
        try:
            # Fetch entire state as JSON
            cmd = ["terraform", "show", "-json"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)  # nosec
            state = json.loads(result.stdout)
            
            # recursive search function for the complex state structure
            def search_resources(root):
                found = []
                # Direct resources
                if 'resources' in root:
                    found.extend(root['resources'])
                # Child modules
                if 'child_modules' in root:
                    for mod in root['child_modules']:
                        found.extend(search_resources(mod))
                return found

            all_resources = []
            if 'values' in state and 'root_module' in state['values']:
                all_resources = search_resources(state['values']['root_module'])

            for r in all_resources:
                if r.get('type') == resource_type and r.get('values', {}).get('id') == physical_id:
                    return r.get('address')
                    
        except Exception as e:
            logger.warning(f"State lookup failed for {physical_id}: {e}")
            
        return None

    def execute_remediation_plan(self, plan: Dict):
        """
        Executes the remediation plan directly using secure subprocess calls.
        """
        import subprocess  # nosec
        import re
        import os
        import shutil

        logger.info("🛡️ Executing ActiveOps Remediation via Secure Subprocess...")
        
        # 0. Safety: Backup Terraform State if it exists
        state_file = "terraform.tfstate"
        if os.path.exists(state_file):
            backup_file = f"{state_file}.backup.{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                shutil.copy2(state_file, backup_file)
                logger.info(f"💾 Safety Backup Created: {backup_file}")
            except Exception as e:
                logger.error(f"⚠️ Failed to create safety backup: {e}. Proceeding with caution.")
        else:
            logger.info("ℹ️ No local terraform.tfstate found. Skipping backup.")

        # Validation Pattern for Instance IDs
        SAFE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9\-]+$")

        success_count = 0
        fail_count = 0

        for r in plan['resources']:
            resource_id = r['id']
            platform = r['platform'].upper()
            
            # 1. Strict Input Validation
            if not SAFE_ID_PATTERN.match(resource_id):
                logger.error("❌ SECURITY ALERT: Invalid Resource ID '%s' detected. Skipping.", resource_id)
                fail_count += 1
                continue

            # 2. Resolve Resource Address
            resource_type = self.RESOURCE_MAPPING.get(platform)
            if not resource_type:
                logger.warning("Unknown platform %s for resource %s. Skipping.", platform, resource_id)
                fail_count += 1
                continue

            # Smart Lookup: Don't guess the name, find it.
            target_address = self._find_resource_in_state(resource_type, resource_id)
            
            if not target_address:
                # Fallback: Try the naive guess only if lookup failed (maybe state is partial)
                # But actually, if it's not in state, 'state rm' will definitely fail.
                # We'll log it as a failure to sync.
                logger.error(f"❌ State Sync Failed: Could not find resource with ID {resource_id} in Terraform state.")
                fail_count += 1
                continue

            cmd = ["terraform", "state", "rm", target_address]

            try:
                logger.info("⚡ Sniping %s...", target_address)
                subprocess.run(cmd, check=True, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # nosec
                success_count += 1
            except subprocess.CalledProcessError as e:
                logger.error("❌ Terraform Execution Failed for %s: %s", resource_id, e.stderr.decode().strip())
                fail_count += 1
            except FileNotFoundError:
                logger.critical("❌ Terraform binary not found! Ensuring 'terraform' is in PATH.")
                return

        logger.info("✅ ActiveOps Complete. Success: %d, Failed: %d", success_count, fail_count)

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
