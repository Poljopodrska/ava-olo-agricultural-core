FROM public.ecr.aws/docker/library/python:3.11-slim

# Critical: Prevent bytecode generation
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV AVA_VERSION=v2.3.1-blue-debug

WORKDIR /app

# Install system dependencies including for psutil
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    procps \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main_modular.py main.py
COPY modules/ modules/
COPY static/ static/
COPY templates/ templates/
COPY database/ database/
COPY database_operations.py .
COPY database_pool.py .
COPY monitoring-dashboards_manifest.json .

# Clean any accidental bytecode
RUN find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
RUN find . -name "*.pyc" -delete 2>/dev/null || true
RUN find . -name "*.pyo" -delete 2>/dev/null || true

# Create non-root user
RUN useradd -m -u 1000 avaolo && chown -R avaolo:avaolo /app
USER avaolo

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/api/v1/health || exit 1

# Run with explicit module path
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]