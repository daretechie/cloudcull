# CloudCull Setup Guide

## Prerequisites
- Python 3.12+
- Node.js 20+ (for dashboard)
- `uv` package manager (recommended)

## Credential Configuration

CloudCull relies on standard SDK credential chains. It does **not** manage keys itself.

### 1. AWS Credentials
Standard Boto3 configuration:
```bash
export AWS_ACCESS_KEY_ID="testing"
export AWS_SECRET_ACCESS_KEY="testing"
export AWS_REGION="us-east-1"
```
*Or use `~/.aws/credentials`*

### 2. Azure Credentials
Uses `DefaultAzureCredential`. Set these environment variables:
```bash
export AZURE_SUBSCRIPTION_ID="your-sub-id"
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
```

### 3. GCP Credentials
Uses Application Default Credentials (ADC):
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

### 4. AI Model Keys
At least one is required for analysis:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# OR
export GOOGLE_API_KEY="AIza..."
# OR
export OPENAI_API_KEY="sk-..."
```

## Simulated Mode (Demo)
To run CloudCull without *any* of the above credentials:
```bash
uv run cloudcull --simulated --dry-run
```
This will generate a high-fidelity mock report.
