# CloudCull Operations Guide

## Automated Audits (GitHub Actions)
The functionality is defined in `.github/workflows/cull_report.yml`.
- **Frequency**: Hourly (`cron: '0 * * * *'`).
- **Trigger**: Push to `main` or Manual Dispatch.
- **Output**: Deploys to `gh-pages` branch.

### Required GitHub Secrets
To run a real multi-cloud audit, add these to **Settings > Secrets and variables > Actions**:
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`
- `GOOGLE_CREDENTIALS_JSON` (Base64 encoded SA key), `GOOGLE_CLOUD_PROJECT`
- `ANTHROPIC_API_KEY` (or other AI keys)

## Runbooks

### S1: Dashboard Not Updating
1.  Check **Actions** tab in GitHub.
2.  If failed, check the logs.
3.  Common cause: Expired API Key or missing `simulated` flag in workflow.

### S2: "Pages Not Found" Error
1.  Go to **Settings > Pages**.
2.  Ensure **Source** is set to **GitHub Actions**.

### S3: Dashboard Remediation Workflow
The "Sniper Console" allows for precision manual remediation:
1.  **Start the Dashboard**: 
    - Build: `cd dashboard && npm run build`
    - Start: `python3 src/dashboard_server.py` (Securely serves at `http://localhost:8080`)
2.  **Analyze**: Review the "Sniper Reasoning" on each card to understand the AI's decision.
3.  **Verify**: Check the metrics (CPU/Network) and owner attribution.
4.  **Snip**: Click the "Copy Kill Command" icon. This copies the exact `terraform state rm` or CLI command for that specific instance.
5.  **Execute**: Paste the command into your terminal to safely remove the resource from your state and infrastructure.

### S4: ActiveOps (Automated Remediation)
For high-speed, autonomous governance:
1.  **Analyze**: Run `uv run python main.py --active-ops`.
2.  **Verify**: CloudCull will directly execute remediation steps via secure `subprocess` and generate `remediation_manifest.json`.
3.  **Approve**: The CLI will prompt for a final confirmation before executing the remediation actions (Physical Stop + State RM).
4.  **Safety**: Before any destructive state removal, CloudCull automatically creates a backup in the `backups/` directory.
5.  **Audit**: Review the `remediation_manifest.json` for a post-mortem of all actions taken.

### S5: Monitoring Platform Health
CloudCull exposes real-time metrics and a secure UI:
1.  **Metrics (Prometheus)**: `http://localhost:8000/metrics` (configurable via `METRICS_PORT`).
2.  **Dashboard (Secure UI)**: `http://localhost:8080` (requires `python3 src/dashboard_server.py`).
3.  **Key Gauges**:
    - `cloudcull_zombies_found_total`: Current count of identified waste.
    - `cloudcull_potential_savings_usd`: Projected monthly savings from pending remediation.

### S6: Partial Remediation Failure
1.  **Scenario**: Physical stop succeeds, but Terraform state removal fails.
2.  **Detection**: CLI logs: "Terraform Execution Failed for [ID]".
3.  **Action**: Manually run the "Copy Kill Command" from the Sniper Console to synchronize the state.
4.  **Verification**: Re-run the audit and confirm the instance is no longer identified.

### S5: Emergency Kill-Switch (CLI)
To verify the kill-switch works without cost:
1.  Run locally with `--dry-run`.
2.  Verify the logs show "Executing Kill-Switch".
3.  ONLY when confident, remove `--dry-run`.

## Security
- **Least Privilege**: The runner only needs `ReadOnly` access for `scan()`.
- **Write Access**: `stop_instance()` requires `ec2:StopInstances` (AWS), `Microsoft.Compute/virtualMachines/deallocate/action` (Azure), etc.
