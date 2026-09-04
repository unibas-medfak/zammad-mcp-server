# Zammad MCP Server Dockerfile

# ---- Build stage: resolve nothing, install exactly what uv.lock pins ----
FROM python:3.14-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

COPY --from=ghcr.io/astral-sh/uv:0.12.7 /uv /bin/uv

WORKDIR /app

# Locked dependencies first; this layer is independent of the source
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

# Then the package itself, installed as a wheel rather than editable
COPY README.md LICENSE ./
COPY src/ ./src/
RUN uv sync --locked --no-dev --no-editable


# ---- Runtime stage: just the virtualenv, no build tooling ----
FROM python:3.14-slim

LABEL maintainer="Open Ticket AI <tobias.bueck@openticketai.com>"
LABEL description="MCP Server for Zammad Helpdesk System"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# The virtualenv is self-contained and pinned to this same /app/.venv path
COPY --from=builder /app/.venv /app/.venv

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port for HTTP transport
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (HTTP transport; override with --transport stdio for local MCP clients)
CMD ["zammad-mcp-server", "--transport", "http", "--host", "0.0.0.0", "--port", "8000"]
