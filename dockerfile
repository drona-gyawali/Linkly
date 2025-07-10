# Using Python slim image for light built
FROM python:3.11-slim

# Setting up environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Setting working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential libpq-dev

# Copy pyproject + lock file
COPY pyproject.toml uv.lock ./

# Install uv (ultra-fast dependency manager)
RUN pip install uv && uv venv && .venv/bin/uv pip install --upgrade pip && .venv/bin/uv pip install -r <(uv pip compile --generate-hashes)

# Add PATH and activate virtualenv
ENV PATH="/app/.venv/bin:$PATH"

# Copy source code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run FastAPI app
CMD ["uvicorn", "linkly.main:app", "--host", "0.0.0.0", "--port", "8000"]
