# CloudCull Operations Guide

## Automated Audits (GitHub Actions)
The functionality is defined in `.github/workflows/cull_report.yml`.
- **Frequency**: Hourly (`cron: '0 * * * *'`).
- **Trigger**: Push to `main` or Manual Dispatch.
- **Output**: Deploys to `gh-pages` branch.

## Runbooks

### S1: Dashboard Not Updating
1.  Check **Actions** tab in GitHub.
2.  If failed, check the logs.
3.  Common cause: Expired API Key or missing `simulated` flag in workflow.

### S2: "Pages Not Found" Error
1.  Go to **Settings > Pages**.
2.  Ensure **Source** is set to **GitHub Actions**.

### S3: Emergency Kill-Switch
To verify the kill-switch works without cost:
1.  Run locally with `--dry-run`.
2.  Verify the logs show "Executing Kill-Switch".
3.  ONLY when confident, remove `--dry-run`.

## Security
- **Least Privilege**: The runner only needs `ReadOnly` access for `scan()`.
- **Write Access**: `stop_instance()` requires `ec2:StopInstances` (AWS), `Microsoft.Compute/virtualMachines/deallocate/action` (Azure), etc.
