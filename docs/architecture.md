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
        JSON -- "ZOMBIE" --> Terraform[IaC Remediator]
        Terraform -->|Generate| Plan[Terraform State Rm Plan]
        JSON -- "ZOMBIE" --> KillSwitch[API Kill-Switch (Optional)]
    end
    
    subgraph "Layer 4: Visibility (Sniper Console)"
        Orchestrator -->|Output| Report[report.json]
        Report -->|Build| Vite[Vite + React Dashboard]
        Vite -->|Feature| AI[AI Reasoning Callouts]
        Vite -->|Feature| Log[Live Sniper Log Terminal]
        Vite -->|Feature| Snip[One-Tap Kill Actions]
        Vite -->|Deploy| Pages[GitHub Pages]
    end
```

## Core Components

### 1. Multi-Cloud Adapters (`adapters/`)
- **Design Principle**: "Unified Interface". All adapters inherit implicitly from a common structural pattern (get_metrics, get_attribution, scan).
- **Resilience**: Each adapter has a `simulated` mode that generates high-fidelity mock data if credentials are missing.

### 2. The AI Brain (`llm/`)
- **Strategy Pattern**: `LLMFactory` allows hot-swapping between `AnthropicProvider`, `GoogleProvider`, etc.
- **Robustness**: Uses regex-based JSON heuristics to survive "chatty" LLM responses.

### 3. Identity Attribution
- **AWS**: Queries `CloudTrail` for `RunInstances` events.
- **Azure**: Queries `Activity Logs` for write operations.
- **GCP**: Queries `Cloud Audit Logs` for insert operations.
- **Why?**: Knowing *who* launched a zombie instance is critical for "Shame-Ops" (accountability).

### 4. Remediation Engine
- **Philosophy**: "GitOps First". We prefer generating `terraform state rm` commands over destructive API calls.
- **ActiveOps Artifacts**:
    - `remediation.sh`: An executable shell script for manual or orchestrated culling.
    - `remediation_manifest.json`: A structured manifest for CI/CD integration.
- **Kill-Switch**: A `--no-dry-run` flag exists for emergency cost control, executing direct API termination.
- **Orchestration**: The `--active-ops` flag triggers automated execution of the remediation artifacts.
