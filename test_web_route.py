#!/usr/bin/env python3
"""
Test web route locally
"""
import uvicorn
from api_gateway_constitutional import app

if __name__ == "__main__":
    print("🏛️ Testing Constitutional Web Interface...")
    print("Starting server on http://localhost:8080")
    print("Test routes:")
    print("  - http://localhost:8080/web/")
    print("  - http://localhost:8080/web/health")
    print("  - http://localhost:8080/health")
    
    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info")