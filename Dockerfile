# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

# Install UV package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies using UV
RUN uv sync --frozen --no-dev

# Copy the rest of the application
COPY . .

# Expose port for Marimo applications
EXPOSE 8080

# Default command - can be overridden in docker-compose or at runtime
CMD ["uv", "run", "marimo", "edit", "--host", "0.0.0.0", "--port", "8080"]
