#!/bin/bash
# 🏛️ CAVA Docker Startup Script for WSL
# Uses Windows Docker Desktop from WSL

echo "🏛️ Starting CAVA Infrastructure..."

# Check if Docker Desktop is running
if ! docker.exe ps > /dev/null 2>&1; then
    echo "❌ Docker Desktop is not running. Please start Docker Desktop on Windows."
    exit 1
fi

# Navigate to the correct directory
cd /mnt/c/Users/HP/ava-olo-constitutional/ava-olo-agricultural-core

# Start CAVA containers using Windows Docker
echo "🚀 Starting CAVA containers..."
docker.exe compose -f docker/docker-compose.cava.yml up -d

# Check status
echo ""
echo "🔍 Checking container status..."
docker.exe ps | grep cava

echo ""
echo "✅ CAVA infrastructure started!"
echo ""
echo "Neo4j Web UI: http://localhost:7474"
echo "Neo4j Bolt: bolt://localhost:7687"
echo "Redis: redis://localhost:6379"
echo ""
echo "To stop: docker.exe compose -f docker/docker-compose.cava.yml down"