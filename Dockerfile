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

# Copy application code
COPY . .

# Copy built dashboard assets to a subfolder for serving if needed
COPY --from=dashboard-builder /app/dashboard/dist ./dashboard/dist

# Default command
ENTRYPOINT ["uv", "run", "python", "main.py"]
CMD ["--simulated", "--dry-run"]
