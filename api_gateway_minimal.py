"""
Minimal API Gateway for deployment safety testing
Deployment fix: 2025-07-19 07:37 CEST
"""
import os
import sys
import traceback
from datetime import datetime

def emergency_log(message):
    """Emergency logging that goes to stdout (shows in AWS logs)"""
    timestamp = datetime.now().isoformat()
    print(f"🚨 EMERGENCY LOG {timestamp}: {message}", flush=True)
    sys.stdout.flush()

emergency_log("=== STARTUP DEBUGGING BEGINS ===")
emergency_log(f"Python version: {sys.version}")
emergency_log(f"Working directory: {os.getcwd()}")
emergency_log(f"Environment variables: {list(os.environ.keys())}")

try:
    emergency_log("Importing FastAPI...")
    from fastapi import FastAPI, HTTPException
    emergency_log("✅ FastAPI imported successfully")
except Exception as e:
    emergency_log(f"❌ FastAPI import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    emergency_log("Creating FastAPI app...")
    app = FastAPI(title="AVA OLO Agricultural Core API", version="1.0.0")
    emergency_log("✅ FastAPI app created successfully")
except Exception as e:
    emergency_log(f"❌ FastAPI app creation failed: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    emergency_log("Importing other modules...")
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse
    from pydantic import BaseModel
    from typing import Dict, Any, Optional, List
    import uvicorn
    import logging
    emergency_log("✅ Basic imports successful")
except Exception as e:
    emergency_log(f"❌ Basic imports failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add CORS middleware
try:
    emergency_log("Adding CORS middleware...")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    emergency_log("✅ CORS middleware added successfully")
except Exception as e:
    emergency_log(f"❌ CORS middleware failed: {e}")
    traceback.print_exc()

# Simple request models
class QueryRequest(BaseModel):
    query: str
    farmer_id: Optional[int] = None

class QueryResponse(BaseModel):
    answer: str
    confidence: float = 0.9
    sources: List[str] = []

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def landing_page():
    """Simple landing page"""
    emergency_log("Root endpoint called - app is running!")
    return """
    <html>
    <head><title>AVA OLO Agricultural Core</title></head>
    <body>
        <h1>AVA OLO Agricultural Core</h1>
        <p>Agricultural intelligence system is running.</p>
        <p><a href="/health">Health Check</a></p>
    </body>
    </html>
    """

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    emergency_log("Health check endpoint called")
    return {
        "status": "healthy",
        "service": "ava-olo-agricultural-core-minimal",
        "version": "1.0.0-minimal-emergency",
        "message": "Minimal API with emergency logging",
        "timestamp": datetime.now().isoformat(),
        "deployment": "2025-07-17-20:31"
    }

# Simple query endpoint
@app.post("/api/v1/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process agricultural query"""
    emergency_log(f"Query endpoint called with: {request.query}")
    return QueryResponse(
        answer=f"Thank you for your agricultural question: '{request.query}'. This is a test response from the API Gateway.",
        confidence=0.9,
        sources=["Test system"]
    )

# Farmers endpoint
@app.get("/api/v1/farmers")
async def get_farmers():
    """Get farmers list"""
    emergency_log("Farmers endpoint called")
    return {
        "farmers": [
            {"id": 1, "name": "Test Farmer", "farm_name": "Test Farm"}
        ]
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    emergency_log("Startup event triggered")
    try:
        emergency_log("Performing startup tasks...")
        # Any startup code here
        emergency_log("✅ Startup completed successfully")
    except Exception as e:
        emergency_log(f"❌ Startup failed: {e}")
        traceback.print_exc()
        raise

emergency_log("=== APP DEFINITION COMPLETE ===")

if __name__ == "__main__":
    emergency_log("Starting uvicorn server...")
    port = int(os.getenv("PORT", 8080))
    emergency_log(f"Using port: {port}")
    try:
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except Exception as e:
        emergency_log(f"❌ Uvicorn failed to start: {e}")
        traceback.print_exc()
        sys.exit(1)# Force rebuild: Sat Jul 19 07:53:19 CEST 2025
