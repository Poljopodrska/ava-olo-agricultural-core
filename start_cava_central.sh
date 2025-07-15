#!/bin/bash
# 🏛️ Start CAVA Central Service
# This ensures CAVA runs as a central service for all app components

echo "🏛️ Starting CAVA Central Service..."
echo "================================="

# Check if CAVA is already running
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ CAVA is already running at http://localhost:8001"
    echo "   All app components will connect to this central instance"
else
    echo "🚀 Starting CAVA service..."
    
    # Check if in dry-run mode
    if [ -z "$CAVA_DRY_RUN_MODE" ]; then
        export CAVA_DRY_RUN_MODE=true
        echo "   Running in DRY-RUN mode (Docker not required)"
    fi
    
    # Start CAVA in background
    nohup python3 implementation/cava/cava_api.py > cava_service.log 2>&1 &
    CAVA_PID=$!
    echo "   CAVA started with PID: $CAVA_PID"
    
    # Write PID to file for later shutdown
    echo $CAVA_PID > cava_service.pid
    
    # Wait for CAVA to be ready
    echo -n "   Waiting for CAVA to be ready"
    for i in {1..30}; do
        if curl -s http://localhost:8001/health > /dev/null 2>&1; then
            echo ""
            echo "✅ CAVA is ready!"
            break
        fi
        echo -n "."
        sleep 1
    done
    
    if ! curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo ""
        echo "❌ CAVA failed to start. Check cava_service.log for details"
        exit 1
    fi
fi

echo ""
echo "🏛️ CAVA Central Service Status:"
echo "================================="
curl -s http://localhost:8001/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8001/health
echo ""
echo "================================="
echo ""
echo "✅ CAVA is running centrally at: http://localhost:8001"
echo "   All registration forms will use this central instance"
echo ""
echo "To stop CAVA: ./stop_cava_central.sh"
echo "To check logs: tail -f cava_service.log"