#!/usr/bin/env python3
import argparse
import datetime
import json
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Dict, List

from prometheus_client import Gauge, start_http_server

# Modular Imports
from .adapters import AdapterRegistry
from .core.pricing import CloudPricing
from .core.remediation import TerraformRemediator
from .core.settings import settings
from .llm.factory import LLMFactory

# Constants
HOURS_PER_MONTH = 730  # Standardized average hours per month

# Define Metrics
ZOMBIE_GAUGE = Gauge('cloudcull_zombies_found_total', 'Total number of zombie instances detected')
SAVINGS_GAUGE = Gauge('cloudcull_potential_savings_usd', 'Potential monthly savings in USD')

# Configure logging
log_formatter = logging.Formatter('%(asctime)s - [CloudCull] - %(levelname)s - %(message)s')
logger = logging.getLogger("CloudCull")
logger.setLevel(settings.log_level)

# Console Handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

# Secure File Handler (Logs/ Directory)
try:
    log_dir = os.path.join(os.getcwd(), "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    # Rotate logs: Max 10MB, keep 5 backups
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "sniper.log"), 
        mode='a', 
        maxBytes=10*1024*1024, 
        backupCount=5
    )
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)
except Exception as e:
    logger.warning("Failed to initialize secure log handler: %s", e)

class DiscoveryService:
    """Encapsulates multi-cloud target discovery."""
    def __init__(self, region: str, simulated: bool):
        self.adapters = AdapterRegistry.get_all_adapters(region, simulated)

    def scan_all(self) -> List[Dict]:
        all_targets = []
        for adapter in self.adapters:
            all_targets.extend(adapter.scan())
        return all_targets

def scrub_metadata(metadata: Dict) -> Dict:
    """Recursively removes sensitive keys from metadata to prevent dashboard exposure."""
    SENSITIVE_KEYS = {'password', 'secret', 'key', 'token', 'auth', 'credential'}
    if not metadata:
        return {}
    
    def recursive_scrub(obj):
        if isinstance(obj, dict):
            return {
                k: ("***SCRUBBED***" if any(s.lower() in k.lower() for s in SENSITIVE_KEYS) 
                    else recursive_scrub(v))
                for k, v in obj.items()
            }
        elif isinstance(obj, list):
            return [recursive_scrub(i) for i in obj]
        return obj

    return recursive_scrub(metadata)

class ConsoleRenderer:
    """Handles all CLI output and formatting, keeping business logic pure."""
    def print_header(self):
        print(f"\n{'='*95}\n| {'PLATFORM':<10} | {'INSTANCE ID':<20} | {'OWNER':<15} | {'SAVINGS/MO':<12} | {'DECISION'} |\n{'='*95}")

    def print_row(self, t: Dict, monthly: float):
        icon = "🧟" if t['status'] == "ZOMBIE" else "✅"
        # Handle None/Unknown prices gracefully
        if monthly is None:
            savings_str = "UNKNOWN"
        else:
            savings_str = f"${monthly:<11,.2f}"
            
        print(f"| {t['platform']:<10} | {t['id']:<20} | {t['owner']:<15} | {savings_str} | {icon} {t['status']:<11} |")

    def print_footer(self, total_savings: float):
        print(f"{'='*95}")
        print(f"💰 POTENTIAL MONTHLY SAVINGS: ${total_savings:,.2f}")
        print(f"{'='*95}\n")

    def print_iac_header(self):
        print("--- SUGGESTED IAC ACTIONS ---")

    def print_iac_action(self, r: Dict):
        print(f"Resource: {r['id']} | Action: {r['suggested_iac_action']}")
    
    def print_iac_footer(self):
        print("-" * 30)


class CloudCullRunner:
    def __init__(self, region: str = "us-east-1", dry_run: bool = True, model: str = "claude", 
                 simulated: bool = False, auto_approve: bool = False, max_workers: int = 10):
        self.dry_run = dry_run
        self.simulated = simulated
        self.auto_approve = auto_approve
        self.max_workers = max_workers
        self.discovery = DiscoveryService(region, simulated)
        self.pricing = CloudPricing()
        self.remediator = TerraformRemediator()
        self.brain = LLMFactory.get_provider(model, simulated=simulated)
        
        logger.info("CloudCull initialized with machine intelligence: %s%s", 
                    model.upper(), " (SIMULATED)" if simulated else "")
        
        if not simulated:
            self._preflight_check()

    def _preflight_check(self):
        """Ensures minimal environmental readiness to prevent late-stage failures."""
        logger.info("🧪 Running Pre-flight Health Checks...")
        errors = []
        
        # 1. Test LLM Connectivity
        try:
            if not self.brain:
                errors.append("LLM Provider initialization failed")
        except Exception as e:
            errors.append(f"LLM Connectivity Check Failed: {e}")

        # 2. Test IaC Tool Availability
        if not self.remediator.check_terraform_binary():
            errors.append("Terraform binary not found in PATH. Remediation will be unavailable.")

        # 3. Test Cloud Adapter Initialization & Active Connectivity
        healthy_adapters = []
        if not self.discovery.adapters:
            errors.append("No cloud adapters initialized")
        else:
            for adapter in self.discovery.adapters:
                if adapter.verify_connection():
                    healthy_adapters.append(adapter)
                else:
                    logger.warning("⚠️  Cloud Connection Verification Failed for %s. This provider will be skipped.", type(adapter).__name__)
        
        # 4. Resilience Decision: Do we have at least ONE way to find waste?
        if not healthy_adapters and self.discovery.adapters:
            errors.append("All initialized cloud adapters failed connectivity verification.")
        
        # We only keep the healthy ones
        self.discovery.adapters = healthy_adapters

        if errors:
            print("\n" + "!"*60)
            print("! CRITICAL ERROR: CloudCull Environment not ready")
            for err in errors:
                print(f"! - {err}")
            print("!"*60 + "\n")
            sys.exit(1)
        
        if not self.discovery.adapters:
            logger.error("No healthy cloud adapters remaining. Exiting.")
            sys.exit(1)
            
        logger.info("✅ Pre-flight checks passed. Launching sniper.")

    def run_audit(self, renderer: ConsoleRenderer = None) -> List[Dict]:
        """The core execution loop."""
        # 1. Discovery
        all_targets = self.discovery.scan_all()
        
        # 2. Parallel Analysis & Classification
        from concurrent.futures import ThreadPoolExecutor
        
        all_results = []
        zombies = []
        total_monthly_savings = 0.0

        if renderer:
            renderer.print_header()

        def analyze_target(t: Dict) -> Dict:
            try:
                llm_report = self.brain.classify_instance(t['metadata'], t['metrics'])
                t['status'] = llm_report.recommendation.decision
                t['reasoning'] = llm_report.recommendation.reasoning
                
                # Pricing Safety: specific handling for None
                rate = self.pricing.get_hourly_rate(t['platform'], t['type'])
                t['rate'] = rate if rate is not None else 0.0 # internal calc use 0, but UI shows Unknown
                t['rate_is_unknown'] = (rate is None)
            except Exception as e:
                logger.error("Failed to analyze target %s: %s", t.get('id', 'unknown'), e)
                t['status'] = "UNKNOWN"
                t['reasoning'] = f"Analysis Error: {e}"
                t['rate'] = 0.0
                t['rate_is_unknown'] = True
            
            return t

        logger.info("📡 Analyzing %d targets in parallel (Workers=%d)...", len(all_targets), self.max_workers)
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            analyzed_targets = list(executor.map(analyze_target, all_targets))

        for t in analyzed_targets:
            if t.get('rate_is_unknown'):
                monthly = None
            else:
                monthly = t['rate'] * HOURS_PER_MONTH
            
            if renderer:
                renderer.print_row(t, monthly)
            
            if t['status'] == "ZOMBIE":
                if monthly:
                    total_monthly_savings += monthly
                zombies.append(t)
            
            # Privacy: Scrub sensitive metadata before final storage/UI
            t['metadata'] = scrub_metadata(t['metadata'])
            all_results.append(t)

        if renderer:
            renderer.print_footer(total_monthly_savings)
        
        # 3. Remediation Planning
        if zombies:
            self._handle_remediation(zombies, all_results, renderer)
        
        return all_results

    def execute_active_ops(self, zombies: List[Dict]):
        """
        The Production Kill-Switch:
        1. Issues Cloud-Native STOP commands to the actual instances.
        2. Removes the resources from Terraform state.
        """
        if not zombies:
            return

        logger.info("🛡️  INITIATING ACTIVEOPS: Neutralizing %d zombies...", len(zombies))
        
        # 1. Cloud-Native Stop (Physical Remediation)
        # We group zombies by platform to use the correct adapter
        success_count = 0
        for z in zombies:
            platform = z['platform'].upper()
            try:
                # Find the matching adapter
                adapter = AdapterRegistry.get_adapter_by_platform(platform, self.discovery.adapters[0].region, self.simulated)
                if adapter:
                    logger.info("⚡ Stopping %s instance %s...", platform, z['id'])
                    adapter.stop_instance(z['id'], z['metadata'])
                    success_count += 1
                else:
                    logger.warning("No adapter found for platform %s to stop instance %s", platform, z['id'])
            except Exception as e:
                logger.error("Failed to stop %s instance %s: %s", platform, z['id'], e)

        # 2. IaC Management (State Remediation)
        if success_count > 0:
            plan = self.remediator.generate_plan(zombies)
            self.remediator.execute_remediation_plan(plan)
            logger.info("✅ ActiveOps Physical & State remediation complete.")
        else:
            logger.warning("ActiveOps aborted: No instances were successfully stopped in the cloud.")

    def _handle_remediation(self, zombies: List[Dict], all_results: List[Dict], renderer: ConsoleRenderer = None):
        iac_plan = self.remediator.generate_plan(zombies)
        
        # Enrich results with IaC actions
        action_map = {r['id']: r['suggested_iac_action'] for r in iac_plan['resources']}
        for r in all_results:
            if r['id'] in action_map:
                r['iac_command'] = action_map[r['id']]
        
        if self.dry_run:
            logger.info("Dry-run: Generating IaC Remediation Plan (Simulation)...")
            if renderer:
                renderer.print_iac_header()
                for r in iac_plan['resources']:
                    renderer.print_iac_action(r)
                renderer.print_iac_footer()


def main():
    parser = argparse.ArgumentParser(description="CloudCull: The Autonomous Multi-Cloud GPU Sniper")
    parser.add_argument("--region", default=settings.aws_region, help="Cloud region to scan")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Simulate without action")
    parser.add_argument("--no-dry-run", action="store_false", dest="dry_run", help="Enable production kill-switch")
    parser.add_argument("--simulated", action="store_true", help="Run in mock mode without cloud credentials")
    parser.add_argument("--model", default=settings.llm_provider, choices=["anthropic", "openai", "google", "groq", "claude", "gemini", "llama"], help="AI Model for analysis")
    parser.add_argument("--active-ops", action="store_true", help="Generate and execute remediation bundle")
    parser.add_argument("--auto-approve", action="store_true", help="Bypass manual confirmation prompts (Use with CAUTION)")
    parser.add_argument("--output", help="Path to save JSON report")
    parser.add_argument("--workers", type=int, default=10, help="Parallel worker count")
    
    args = parser.parse_args()

    # Start Prometheus Metrics Server
    try:
        start_http_server(settings.metrics_port)
        logger.info(f"📊 Prometheus Metrics exposed at http://localhost:{settings.metrics_port}/metrics")
    except Exception as e:
        logger.warning(f"Failed to start Metrics Server: {e}")

    renderer = ConsoleRenderer()

    runner = CloudCullRunner(
        region=args.region, 
        dry_run=args.dry_run, 
        model=args.model, 
        simulated=args.simulated,
        auto_approve=args.auto_approve,
        max_workers=args.workers
    )
    
    # Pass renderer solely for UI output
    results = runner.run_audit(renderer=renderer)

    if any(r['status'] == "ZOMBIE" for r in results):
        zombies = [r for r in results if r['status'] == "ZOMBIE"]
        plan = runner.remediator.generate_plan(zombies)
        runner.remediator.save_manifest(plan)
        
        if args.active_ops:
            logger.info("📡 ACTIVEOPS TRIGGERED: Executing Remediation Plan...")
            
            if not args.auto_approve:
                confirm = input(f"CRITICAL: Execute automated remediation for {len(zombies)} targets? [y/N]: ")
                if confirm.lower() != 'y':
                    logger.info("❌ ActiveOps aborted by operator.")
                    return

            try:
                # SECURE EXECUTION: Cloud Stop + State RM
                runner.execute_active_ops(zombies)
            except Exception as e:
                logger.error("❌ ACTIVEOPS FAILED: %s", e)

    if args.output:
        with open(args.output, "w", encoding='utf-8') as f:
            # Filter None prices for robust JSON dump
            safe_results = []
            for r in results:
                safe_r = r.copy()
                if safe_r.get('rate_is_unknown'):
                    safe_r['rate'] = 0.0 # Clean up for JSON consumer
                safe_results.append(safe_r)

            json.dump({
                "summary": {
                    "total_monthly_savings": sum(r['rate'] * HOURS_PER_MONTH for r in safe_results if r['status'] == "ZOMBIE"),
                    "zombie_count": sum(1 for r in safe_results if r['status'] == "ZOMBIE"),
                    "timestamp": datetime.datetime.now(datetime.UTC).isoformat()
                },
                "instances": safe_results
            }, f, indent=2)
        logger.info("JSON Report saved to %s", args.output)

    # Push Final Metrics
    z_count = sum(1 for r in results if r['status'] == "ZOMBIE")
    # Handle unknown rates safely for the sum
    safe_savings = sum(r['rate'] * HOURS_PER_MONTH for r in results if r['status'] == "ZOMBIE" and not r.get('rate_is_unknown'))
    
    ZOMBIE_GAUGE.set(z_count)
    SAVINGS_GAUGE.set(safe_savings)
    logger.info(f"📈 Metrics Updated: {z_count} Zombies, ${safe_savings:,.2f} Savings")

if __name__ == "__main__":
    main()
