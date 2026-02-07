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
COPY src/watchers/gmail.py ./src/watchers/
COPY src/lib/ ./src/lib/

# Set environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Run Gmail watcher
CMD ["python", "-m", "src.watchers.gmail"]
