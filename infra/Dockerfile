# Multi-stage Dockerfile for CloudCull
# 1. Build Dashboard
FROM node:20-alpine AS dashboard-builder
WORKDIR /app/dashboard
COPY dashboard/package*.json ./
RUN npm ci
COPY dashboard/ ./
RUN npm run build

# 2. Final Python Image
FROM python:3.12-slim
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uv/bin/
ENV PATH="/uv/bin:${PATH}"

# Copy requirements and install
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Security Hardening: Create non-root user
RUN groupadd -r cloudcull && useradd -r -g cloudcull cloudcull

# Copy application code and change ownership
COPY --chown=cloudcull:cloudcull src/ ./src/
COPY --chown=cloudcull:cloudcull config/ ./config/
COPY --chown=cloudcull:cloudcull pyproject.toml uv.lock ./

# Copy built dashboard assets
COPY --from=dashboard-builder --chown=cloudcull:cloudcull /app/dashboard/dist ./dashboard/dist

# Switch to non-root user
USER cloudcull

# Default command
ENTRYPOINT ["uv", "run", "cloudcull"]
CMD ["--simulated", "--dry-run"]
