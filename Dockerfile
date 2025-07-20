# AVA OLO Monitoring API with Constitutional Design
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY monitoring_api_constitutional.py .
COPY config.py .

# Copy design system
COPY shared/ ./shared/

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=development
ENV PORT=8080
ENV DEV_ACCESS_KEY=ava-dev-2025-secure-key

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "-m", "uvicorn", "monitoring_api_constitutional:app", "--host", "0.0.0.0", "--port", "8080"]