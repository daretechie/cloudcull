# CloudCull Architecture: "The Sniper Pattern"

## Overview
CloudCull uses a linear, autonomous governance flow we call **"The Sniper Pattern"**. Unlike traditional dashboards that simply *show* data, CloudCull is designed to *act* on data.

## System Design
The system is composed of four decoupled layers:

```mermaid
graph TD
    Trigger[Cron / GitHub Action] -->|Hourly| Orchestrator[CloudCull Runner (main.py)]
    
    subgraph "Layer 1: Discovery (Adapters)"
        Orchestrator -->|Probe| AWS[AWS Adapter (Boto3)]
        Orchestrator -->|Probe| Azure[Azure Adapter (SDK)]
        Orchestrator -->|Probe| GCP[GCP Adapter (Client)]
    end
    
    subgraph "Layer 2: Intelligence (Brain)"
        Orchestrator -->|Classify| LLM[LLM Factory (Claude/Gemini)]
        LLM -->|Extract| JSON[Structured JSON Decision]
    end
    
    subgraph "Layer 3: Governance (Remediation)"
        JSON -- "ZOMBIE" --> Unified["Unified Remediation Flow"]
        Unified -->|Step 1| Stop[API Physical Stop]
        Unified -->|Step 2| Terraform[IaC State RM]
    end
    
    subgraph "Layer 4: Visibility (Sniper Console)"
        Orchestrator -->|Output| Report[report.json]
        Report -->|Build| Vite[Vite + React Dashboard]
        Vite -->|Feature| AI[AI Reasoning Callouts]
        Vite -->|Feature| Log[Live Sniper Log Terminal]
        Vite -->|Feature| Snip[One-Tap Kill Actions]
        Vite -->|Feature| SnipAction[Sanitized CLI Actions]
        Vite -->|Deploy| Pages[GitHub Pages]
    end
```

## Core Components

### 1. Multi-Cloud Adapters (`adapters/`)
- **Design Principle**: "Unified Interface". All adapters inherit from `AbstractAdapter`.
- **Resilience**: Hardened with specific SDK exception handling (ClientError, AzureError, etc.) to improve diagnostic observability.
- **Efficiency**: Implements target batching to solve N+1 discovery bottlenecks.

### 2. The AI Brain (`llm/`)
- **Strategy Pattern**: `LLMFactory` allows hot-swapping between `AnthropicProvider`, `GoogleProvider`, etc.
- **Robustness**: Uses advanced JSON extraction heuristics to handle markdown-wrapped or chatty responses. Survives non-JSON snippets.
- **Parallelization**: The `CloudCullRunner` utilizes a `ThreadPoolExecutor` to classify multiple instances concurrently, achieving O(1) analysis time relative to target count.

### 3. Fail-Fast Reliability (Pre-flight)
- **Preflight Checks**: Before scanning, the orchestrator verifies LLM connectivity and cloud adapter initialization to prevent late-stage pipeline failures.

### 4. Identity Attribution (Shame-Ops)
- **AWS**: Queries `CloudTrail` for `RunInstances` events.
- **Azure**: Queries `Activity Logs` for write operations.
- **GCP**: Queries `Cloud Audit Logs` for insert operations.
- **Why?**: Knowing *who* launched a zombie instance is critical for visibility and cost attribution.

### 5. Remediation Engine
- **Philosophy**: "GitOps First". We generate sanitized `terraform state rm` commands to reconcile infrastructure state.
- **Security**: All shell inputs (IDs, Platforms, Owners) are sanitized using `shlex.quote` to eliminate command injection vectors.
- **ActiveOps Artifacts**:
    - `remediation_manifest.json`: A structured manifest for CI/CD integration and auditing.
- **Security**: No intermediate shell scripts are generated. All actions are executed via `subprocess.run` with list-based arguments and `shell=False`.
- **Kill-Switch**: A `--no-dry-run` flag exists for direct API termination.
- **Orchestration**: The `--active-ops` flag combined with `--auto-approve` enables headless, autonomous remediation.
# Design Principles: The "Sniper" Philosophy

CloudCull is built on specific architectural decisions that differentiate it from generic scripts or "black box" SaaS tools.

## 1. CLI-First & Pipeline-Ready
**Rationale:** In high-stakes operations, a GUI is often a bottleneck. CloudCull is designed to be:
*   **Embeddable:** Runs inside GitHub Actions, Jenkins, or GitLab CI.
*   **Stateless:** No database required for the core logic; state is derived from the Cloud API itself.
*   **Composable:** The JSON output can be piped into `jq`, Slack webhooks, or other tools.

## 2. The Modular Adapter Pattern
**Rationale:** Cloud provider APIs are messy and inconsistent. We isolate this "noise" in the `adapters/` layer.
*   **Significance:** This ensures the `core/` logic never needs to change just because AWS updates an API version. It allows us to add new providers (e.g., Oracle Cloud, DigitalOcean) without touching the decision engine.

## 3. Identity Attribution as a Core Feature
**Rationale:** Finding a zombie instance is easy. Finding *who* launched it is the real problem.
*   **Implementation:** We treat `CloudTrail`, `Azure Activity Logs`, and `GCP Audit Logs` as first-class citizens.
*   **Value:** This transforms the tool from a "Cost Reporter" to a "Governance Enforcer."

## 4. GitOps-Aware Remediation
**Rationale:** Deleting resources via API (`boto3.delete_instance`) is dangerous in an IaC-managed environment. It causes state drift.
*   **Solution:** CloudCull prefers to generate a **Terraform Plan** (`terraform state rm`) or a **Pull Request** to scale down `min_size` in an ASG. This respects the "Infrastructure as Code" source of truth.

## 5. Multi-Model Intelligence (Vendor Independence)
**Rationale:** We do not lock you into OpenAI. The `LLMFactory` allows you to route requests based on:
*   **Privacy:** Use a locally hosted Llama via Groq.
*   **Cost:** Use Gemini Flash for high-volume scanning.
*   **Smarts:** Use Claude or GPT-4o for complex reasoning.

## 6. Visibility as a Catalyst for Action
**Rationale:** Dashboards that only show "Potential Savings" often lead to analysis paralysis.
*   **The Sniper Console:** We transform the dashboard into a "Sniper Console" by providing **AI Reasoning Callouts** and **One-Tap Snip** controls. 
*   **Result:** By showing exactly *why* an instance is a zombie and providing the *exact command* to kill it, we remove the friction between detection and remediation.
