# Use Python slim image
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Working directory
WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y build-essential libpq-dev curl && apt-get clean

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install uv globally
RUN pip install uv

# Create and activate virtual environment
RUN uv venv && .venv/bin/uv sync --locked

# Add virtualenv to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy the rest of the source code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run app (with PORT fallback)
CMD ["sh", "-c", "uvicorn linkly.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
