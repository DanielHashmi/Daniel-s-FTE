FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY .claude/ ./.claude/

# Set environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Run orchestrator
CMD ["python", "-m", "src.orchestration.orchestrator"]
