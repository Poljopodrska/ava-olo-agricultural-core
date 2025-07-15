#!/bin/bash
# 🏛️ CAVA AWS Deployment Script
# Run this on your EC2 instance after git pull

set -e

echo "🏛️ Deploying CAVA to AWS..."
echo "================================="

# 1. Check environment
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not set!"
    exit 1
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY not set!"
    exit 1
fi

# 2. Install dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# 3. Stop existing CAVA if running
echo "🛑 Stopping existing CAVA service..."
if [ -f cava_service.pid ]; then
    kill $(cat cava_service.pid) 2>/dev/null || true
    rm cava_service.pid
fi

# 4. Start Docker containers (if using Docker)
if [ "$USE_DOCKER" = "true" ]; then
    echo "🐳 Starting Docker containers..."
    docker-compose -f docker/docker-compose.cava.yml up -d
else
    echo "⏭️ Skipping Docker (using managed services)"
fi

# 5. Run database migrations
echo "📊 Setting up CAVA schema..."
python3 -c "
import asyncio
from implementation.cava.database_connections import CAVADatabaseManager

async def setup():
    manager = CAVADatabaseManager()
    await manager.connect_all()
    # Create schema if needed
    await manager.postgresql.execute_query('''
        CREATE SCHEMA IF NOT EXISTS cava;
        
        CREATE TABLE IF NOT EXISTS cava.conversation_sessions (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(255) UNIQUE NOT NULL,
            farmer_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS cava.intelligence_log (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(255),
            message_type VARCHAR(100),
            llm_response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    await manager.close_all()
    print('✅ Database schema ready')

asyncio.run(setup())
"

# 6. Start CAVA service
echo "🚀 Starting CAVA service..."
export CAVA_DRY_RUN_MODE=false
nohup python3 implementation/cava/cava_api.py > /var/log/cava/cava_api.log 2>&1 &
echo $! > cava_service.pid

# 7. Wait for service to be ready
echo -n "⏳ Waiting for CAVA to be ready"
for i in {1..30}; do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo ""
        echo "✅ CAVA is ready!"
        break
    fi
    echo -n "."
    sleep 1
done

# 8. Verify deployment
echo ""
echo "🔍 Verifying deployment..."
HEALTH=$(curl -s http://localhost:8001/health)
echo "Health check: $HEALTH"

echo ""
echo "================================="
echo "✅ CAVA deployed successfully!"
echo "API endpoint: http://localhost:8001"
echo "Logs: /var/log/cava/cava_api.log"
echo "PID file: cava_service.pid"