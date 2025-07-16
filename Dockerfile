# Use slim Python image
FROM python:3.12-slim

# Environment setup
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set workdir
WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y build-essential libpq-dev curl && apt-get clean

# Copy dependencies
COPY pyproject.toml uv.lock ./

# Install uv
RUN pip install uv

# Create venv with uv
RUN uv venv

# Add virtualenv to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Sync dependencies from lockfile
RUN uv sync --locked

# Copy application code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Start server (Railway sets $PORT)
CMD ["sh", "-c", "uvicorn linkly.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
