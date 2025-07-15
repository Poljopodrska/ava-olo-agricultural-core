#!/bin/bash
# 🏛️ Stop CAVA Central Service

echo "🏛️ Stopping CAVA Central Service..."

if [ -f cava_service.pid ]; then
    PID=$(cat cava_service.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        echo "✅ CAVA service (PID: $PID) stopped"
        rm cava_service.pid
    else
        echo "⚠️ CAVA service not running (PID: $PID not found)"
        rm cava_service.pid
    fi
else
    # Try to find CAVA process
    CAVA_PID=$(ps aux | grep "cava_api.py" | grep -v grep | awk '{print $2}')
    if [ -n "$CAVA_PID" ]; then
        kill $CAVA_PID
        echo "✅ CAVA service (PID: $CAVA_PID) stopped"
    else
        echo "⚠️ CAVA service not running"
    fi
fi