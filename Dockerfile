FROM python:3.11-slim

# Critical: Prevent bytecode generation
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV AVA_VERSION=v3.3.0-ecs-ready

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main_modular.py main.py
COPY modules/ modules/
COPY implementation/ implementation/
COPY templates/ templates/
COPY static/ static/

# Copy CAVA files
COPY cava_registration_llm.py .
COPY cava_registration_engine.py .

# Copy other necessary files
COPY language_processor.py .
COPY database_operations.py .
COPY api_gateway_constitutional_ui.py .
COPY agricultural-core_manifest.json .

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
  CMD python -c "import requests; requests.get('http://localhost:8080/health').raise_for_status()"

# Run with explicit module path
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]