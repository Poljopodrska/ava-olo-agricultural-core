# AVA OLO Agricultural Core Service - v4.12.0
FROM --platform=linux/amd64 public.ecr.aws/docker/library/python:3.11-slim

# Cache busting
ARG CACHEBUST=1
RUN echo "Cache bust: ${CACHEBUST}"

# Build arguments
ARG GITHUB_SHA
ARG GITHUB_REF
ARG BUILD_TIME

# Environment variables to prevent caching
ENV PIP_NO_CACHE_DIR=1
ENV PYTHONDONTWRITEBYTECODE=1

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

# Verify main.py exists
RUN test -f main.py || (echo "ERROR: main.py not found!" && exit 1)

# Print build info for verification
RUN echo "Build completed at: $(date)" > /build-info.txt
RUN echo "Git SHA: ${GITHUB_SHA}" >> /build-info.txt
RUN echo "Cachebust: ${CACHEBUST}" >> /build-info.txt
RUN echo "✅ Build complete with all dependencies" >> /build-info.txt

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production
ENV PORT=8080
ENV VERSION=v4.12.0

# Embed Git information
ENV GITHUB_SHA=${GITHUB_SHA}
ENV GITHUB_REF=${GITHUB_REF}
ENV BUILD_TIME=${BUILD_TIME}

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]