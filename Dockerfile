# AVA OLO Agricultural Core Service
FROM public.ecr.aws/docker/library/python:3.11-slim

# Build arguments for Git verification
ARG GITHUB_SHA
ARG GITHUB_REF
ARG BUILD_TIME
ARG CACHEBUST

# Enforce Git-based builds only
RUN if [ -z "$GITHUB_SHA" ]; then \
    echo "❌ ERROR: Builds MUST come from GitHub Actions!"; \
    echo "This build is attempting to bypass Git deployment controls."; \
    echo "All production deployments must be traceable to Git commits."; \
    exit 1; \
fi

WORKDIR /app

# Install system dependencies including gcc for psutil
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application code
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production
ENV PORT=8080
ENV VERSION=v3.3.2

# Embed Git information for security verification
ENV GITHUB_SHA=${GITHUB_SHA}
ENV GITHUB_REF=${GITHUB_REF}
ENV BUILD_TIME=${BUILD_TIME}

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]# Force rebuild: 1753519614
