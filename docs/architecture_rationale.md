# Architecture Rationale: The Sniper Pattern

## Why CLI-First?
In high-ticket FinOps, execution SPEED and PORTABILITY are more valuable than a complex UI. A CLI-first tool can be:
- Integrated into a GitHub Action runner.
- Scaled across 100+ AWS accounts in minutes.
- Included in a secure DevOps pipeline.

## The Adapter Pattern
By separating `adapters/` from `core/`, we isolate the "Cloud Noise." Each adapter handles the unique API quirks of its provider, while the `core/` engine makes decisions based on normalized data.

## Identity Attribution via CloudTrail
We use `boto3.client('cloudtrail')` to find instance owners. This transforms a cost report into a **Governance Audit**, justifying the premium "Architect" rate.

## IaC-First Remediation
Directly deleting instances via API is risky. Generating a `terraform state rm` command or a PR to a separate Repo proves you respect the infrastructure-as-code state of a modern enterprise.
