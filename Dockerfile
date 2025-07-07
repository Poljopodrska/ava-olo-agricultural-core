# Single-stage Dockerfile for AWS App Runner
FROM python:3.11-slim

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies using pip3
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Verify uvicorn is installed
RUN python3 -m pip list | grep uvicorn

# Expose port for App Runner
EXPOSE 8080

# Start command using python3
CMD ["python3", "-m", "uvicorn", "api_gateway_simple:app", "--host", "0.0.0.0", "--port", "8080"]