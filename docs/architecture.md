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
        Report -->|Serve| Srv[Secure Server (Python)]
        Srv -->|API| Vite[Vite + React Dashboard]
        Vite -->|Feature| AI[AI Reasoning Callouts]
        Vite -->|Feature| Log[Secure Terminal Stream]
        Vite -->|Feature| Snip[One-Tap Kill Actions]
    end
```

## Core Components

### 1. Multi-Cloud Adapters (`adapters/`)
- **Design Principle**: "Unified Interface". All adapters inherit from `AbstractAdapter`.
- **Scalability**: AWS adapter implements **Paginators** for accounts with >50 instances.
- **Precision**: GCP adapter implements real-time **Identity Attribution** via Cloud Audit Logs.

### 2. The AI Brain (`llm/`)
- **Strategy Pattern**: `LLMFactory` allows hot-swapping between `AnthropicProvider`, `GoogleProvider`, etc.
- **Robustness**: Uses advanced JSON extraction heuristics to handle markdown-wrapped or chatty responses.
- **Parallelization**: Parallel classification achieving O(1) analysis time.

### 3. Fail-Fast Reliability (Pre-flight)
- **Preflight Checks**: Verifies LLM connectivity and active cloud credentials before launch.

### 4. Remediation Engine
- **Philosophy**: "GitOps First". We generate sanitized `terraform state rm` commands.
- **Integrity**: Implements **State Lookup**—dynamically finding the correct resource address in `.tfstate` to prevent "blind" deletion failures.
- **Safety**: Automated state backups before destructive actions.

### 5. Secure Visibility
- **Secure Server**: `src/dashboard_server.py` serves the dashboard via a hardened Python backend.
- **API Guard**: Replaces insecure direct file access with specific API endpoints (`/api/logs`, `/api/report`) that enforce path-safe binary reads.

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
