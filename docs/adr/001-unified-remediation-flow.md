# ADR-001: Unified Remediation Flow (Physical Stop + State Removal)

## Status
Accepted

## Context
Originally, CloudCull followed a "GitOps First" philosophy, relying solely on `terraform state rm` to "remove" resources from the managed environment. However, this created a critical failure mode where instances continued to run and incur costs while being orphaned from infrastructure management (IaC).

## Decision
We will transition to a **Unified Remediation Flow** as the system default. During an `ActiveOps` cycle, the system will:
1.  **Issue a Cloud-Native Stop Command**: Using the respective cloud provider API (Boto3, Azure SDK, Google Client) to deallocate or stop the resource physically.
2.  **Perform Terraform State Removal**: Only if the physical stop is triggered, the system will remove the resource from the Terraform state to avoid IaC drift.

## Rationale
- **Cost Assurance**: Ensures that costs actually stop when a "Zombie" is identified.
- **Safety**: Stopping/Deallocating is less destructive than Termination/Deletion, allowing for easier rollback if a false positive occurs.
- **Sanity**: Prevents "Orphaned Zombies" that are no longer visible in Terraform plan output but still active in the cloud account.

## Consequences
- **Permission Requirements**: The service account/role running CloudCull now requires write permissions (e.g., `ec2:StopInstances`).
- **Complexity**: The orchestrator must now track physical stop status before attempting state manipulation.
- **Visibility**: Documentation must be updated to clearly state that CloudCull is now an *active* termination agent, not just an *observability* tool.
