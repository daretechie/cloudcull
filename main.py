#!/usr/bin/env python3
import logging
import argparse

# Modular Imports
from adapters.aws import AWSAdapter
from core.pricing import CloudPricing
from llm.factory import LLMFactory
from integrations.remediation import TerraformRemediator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [CloudCull] - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CloudCull")

class CloudCullRunner:
    def __init__(self, region: str = "us-east-1", dry_run: bool = True, model: str = "claude", simulated: bool = False):
        self.dry_run = dry_run
        self.aws = AWSAdapter(region=region, simulated=simulated)
        
        # Multi-Cloud Adapters
        from adapters.azure import AzureAdapter
        from adapters.gcp import GCPAdapter
        self.azure = AzureAdapter(simulated=simulated)
        self.gcp = GCPAdapter(simulated=simulated)
        
        self.pricing = CloudPricing()
        self.remediator = TerraformRemediator()
        
        # Unified AI Brain
        self.brain = LLMFactory.get_provider(model, simulated=simulated)
        logger.info("CloudCull initialized with machine intelligence: %s%s", 
                    model.upper(), " (SIMULATED)" if simulated else "")

    def run_audit(self):
        """The core execution loop."""
        # 1. Discovery (Multi-Cloud Aggregation)
        all_targets = []
        all_targets.extend(self.aws.scan())
        all_targets.extend(self.azure.scan())
        all_targets.extend(self.gcp.scan())
        
        # 2. Analysis & Classification
        zombies = []
        all_results = []

        print(f"\n{'='*95}\n| {'PLATFORM':<10} | {'INSTANCE ID':<20} | {'OWNER':<15} | {'SAVINGS/MO':<12} | {'DECISION'} |\n{'='*95}")
        
        total_monthly_savings = 0.0

        for t in all_targets:
            # Classification
            llm_report = self.brain.classify_instance(t['metadata'], t['metrics'])
            decision = llm_report.recommendation.decision
            
            t['status'] = decision
            t['rate'] = self.pricing.get_hourly_rate(t['platform'], t['type'])
            
            monthly = t['rate'] * 24 * 30
            icon = "🧟" if decision == "ZOMBIE" else "✅"
            
            print(f"| {t['platform']:<10} | {t['id']:<20} | {t['owner']:<15} | ${monthly:<11,.2f} | {icon} {decision:<11} |")
            
            if decision == "ZOMBIE":
                total_monthly_savings += monthly
                zombies.append(t)
            
            all_results.append(t)

        print(f"{'='*95}")
        print(f"💰 POTENTIAL MONTHLY SAVINGS: ${total_monthly_savings:,.2f}")
        
        # The "Wow" Output Requirement
        for z in zombies:
            print(f"✅ Found idle {z['type']}. Launched by: @{z['owner']}. Potential Savings: ${z['rate'] * 24 * 30:,.2f}/mo.")
            
        print(f"{'='*95}\n")

        # 3. Remediation & IaC Generation
        if zombies:
            iac_plan = self.remediator.generate_plan(zombies)
            
            if self.dry_run:
                logger.info("Dry-run: Generating IaC Remediation Plan (Simulation)...")
                print("--- SUGGESTED IAC ACTIONS ---")
                for r in iac_plan['resources']:
                    print(f"Resource: {r['id']} | Action: {r['suggested_iac_action']} | Owner: {r['owner']}")
                print("-" * 30)
            else:
                # Execution
                confirm = input(f"CRITICAL: Terminate {len(zombies)} zombie instances? [y/N]: ")
                if confirm.lower() == 'y':
                    for z in zombies:
                        platform = z['platform'].lower()
                        if platform == 'aws':
                            self.aws.stop_instance(z['id'])
                        elif platform == 'azure':
                            # Pass name and resource_id
                            self.azure.stop_instance(z['id'], z['metadata']['resource_id'])
                        elif platform == 'gcp':
                            # Pass zone and name
                            self.gcp.stop_instance(z['metadata']['zone'], z['id'])
                    print("\n🛡️  CULL COMPLETE. Infrastructure hardened.")
                else:
                    print("\n❌ Execution aborted by user.")
        
        return all_results

def main():
    parser = argparse.ArgumentParser(description="CloudCull: The Autonomous Multi-Cloud GPU Sniper")
    parser.add_argument("--region", default="us-east-1", help="Cloud region to scan")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Simulate without action")
    parser.add_argument("--no-dry-run", action="store_false", dest="dry_run", help="Enable production kill-switch")
    parser.add_argument("--simulated", action="store_true", help="Run in mock mode without cloud credentials")
    parser.add_argument("--model", default="claude", choices=["claude", "gemini", "llama"], help="AI Model for analysis")
    parser.add_argument("--output", help="Path to save JSON report")
    
    args = parser.parse_args()

    runner = CloudCullRunner(
        region=args.region, 
        dry_run=args.dry_run, 
        model=args.model, 
        simulated=args.simulated
    )
    results = runner.run_audit()

    if args.output:
        import json
        import datetime
        with open(args.output, "w", encoding='utf-8') as f:
            json.dump({
                "summary": {
                    "total_monthly_savings": sum(r['rate'] * 24 * 30 for r in results if r['status'] == "ZOMBIE"),
                    "zombie_count": sum(1 for r in results if r['status'] == "ZOMBIE"),
                    "timestamp": datetime.datetime.now(datetime.UTC).isoformat()
                },
                "instances": results
            }, f, indent=2)
        logger.info("JSON Report saved to %s", args.output)

if __name__ == "__main__":
    main()
