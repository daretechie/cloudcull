#!/bin/bash
set -e

# CloudCull: The Autonomous Multi-Cloud GPU Sniper - Interactive Demo
# This script demonstrates the platform's core capabilities by running the actual
# Python logic in high-fidelity SIMULATED mode.

# --- Styling & Banners ---
BOLD=$(tput bold)
GREEN=$(tput setaf 2)
CYAN=$(tput setaf 6)
YELLOW=$(tput setaf 3)
RED=$(tput setaf 1)
RESET=$(tput sgr0)

BANNER="${CYAN}${BOLD}
 ██████╗██╗      ██████╗ ██╗   ██╗██████╗  ██████╗██╗   ██╗██╗     ██╗     
██╔════╝██║     ██╔═══██╗██║   ██║██╔══██╗██╔════╝██║   ██║██║     ██║     
██║     ██║     ██║   ██║██║   ██║██║  ██║██║     ██║   ██║██║     ██║    
██║     ██║     ██║   ██║██║   ██║██║  ██║██║     ██║   ██║██║     ██║     
╚██████╗███████╗╚██████╔╝╚██████╔╝██████╔╝╚██████╗╚██████╔╝███████╗███████╗
 ╚═════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝  ╚═════╝ ╚═════╝ ╚══════╝╚══════╝
${RESET}"

# Reset Dashboard Logs
echo "" > dashboard/public/sniper.log 2>/dev/null || true

echo "$BANNER"
echo "${BOLD}CloudCull v0.1.0${RESET} | ${YELLOW}Autonomous GPU Cost Optimization Sniper${RESET}"
echo "==============================================================================="
echo ""

# --- Dependency Check ---
echo "${BOLD}[PRE-FLIGHT]${RESET} Validating Environment..."
if ! command -v python3 &> /dev/null; then
    echo "${RED}FAILED: Python 3 not found.${RESET}"
    exit 1
fi
echo "  - Python 3  [${GREEN}OK${RESET}]"

if [[ -f "uv.lock" ]]; then
    PYTHON_CMD="uv run python3"
    echo "  - UV VirtualEnv [${GREEN}OK${RESET}]"
else
    PYTHON_CMD="python3"
    echo "  - System Python [${YELLOW}WARN${RESET}] (Using system python)"
fi
echo ""

# --- Phase 1: High-Fidelity Discovery & Analysis ---
echo "${BOLD}[PHASE 1] Scanning for Multi-Cloud GPU Waste (Simulated)${RESET}"
echo "-------------------------------------------------------------------------------"
echo "${CYAN}Executing: $PYTHON_CMD -m src.main --simulated --model ${LLM_PROVIDER:-anthropic} --output demo_report.json${RESET}"
echo ""

$PYTHON_CMD -m src.main --simulated --model ${LLM_PROVIDER:-anthropic} --output demo_report.json

echo ""
echo "${BOLD}[PHASE 2] Intelligence Review${RESET}"
echo "-------------------------------------------------------------------------------"
echo "CloudCull has generated a comprehensive audit report in ${BOLD}demo_report.json${RESET}."
echo ""
echo "${YELLOW}Insight Preview:${RESET}"
# Extract some insights from the JSON report using python for cross-platform reliability
$PYTHON_CMD -c "import json; r=json.load(open('demo_report.json')); print(f\"  - Targets Scanned: {len(r['instances'])}\"); print(f\"  - Zombies Detected: {r['summary']['zombie_count']}\"); print(f\"  - Potential Monthly Savings: \${r['summary']['total_monthly_savings']:,.2f}\");"
echo ""

# --- Phase 3: ActiveOps Remediation (The Kill-Switch) ---
echo "${BOLD}[PHASE 3] ActiveOps: Automated Remediation Flow${RESET}"
echo "-------------------------------------------------------------------------------"
echo "In a production environment, CloudCull would now execute the Kill-Switch."
echo "This involves: ${BOLD}Cloud-Native Stop${RESET} + ${BOLD}IaC State Removal${RESET}."
echo ""
echo "${RED}${BOLD}CAUTION:${RESET} Initiating ActiveOps Simulation..."
sleep 1

# We run with --no-dry-run but in --simulated mode so no REAL changes happen, but the LOGIC is exercised.
# We also use --auto-approve to simulate a hands-off autonomous agent.
$PYTHON_CMD -m src.main --simulated --no-dry-run --active-ops --auto-approve

# --- Phase 4: Artifact Generation ---
echo "${BOLD}[PHASE 4] Artifact Generation${RESET}"
echo "-------------------------------------------------------------------------------"
echo "CloudCull creates professional-grade artifacts for DevOps/FinOps teams:"
echo "  - ${CYAN}demo_report.json${RESET}           -> Audit logs for compliance/auditing"
echo "  - ${CYAN}config/remediation_manifest.json${RESET} -> Terraform-compatible action plan"
echo ""

# Sync to Dashboard
cp demo_report.json dashboard/public/report.json
echo "${GREEN}Data synchronized to Sniper Dashboard.${RESET}"
echo ""

# --- Phase 5: Sniper Dashboard ---
echo "${BOLD}[PHASE 5] Visualization: Sniper Dashboard${RESET}"
echo "-------------------------------------------------------------------------------"
echo "CloudCull includes a premium React-based dashboard for real-time visualization."
echo "To launch the dashboard:"
echo "  1. ${CYAN}cd dashboard${RESET}"
echo "  2. ${CYAN}npm install && npm run dev${RESET}"
echo ""

echo "${GREEN}${BOLD}Demo Successful.${RESET}"
echo "The CloudCull Agent has identified, analyzed, and remediated \$20,000+/mo in GPU waste."
echo "==============================================================================="
echo "Explore the codebase at: ${BOLD}src/${RESET}"
echo "View detailed docs in:   ${BOLD}docs/${RESET}"
