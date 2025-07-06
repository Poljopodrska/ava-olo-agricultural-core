# Single-stage Dockerfile to ensure all dependencies are available
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Start command
CMD ["uvicorn", "api_gateway_simple:app", "--host", "0.0.0.0", "--port", "8080"]