#!/usr/bin/env python3
"""
EMERGENCY MINIMAL SERVICE - v3.5.40
Absolute minimum to restore service while diagnosing deployment pipeline
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse, HTMLResponse

app = FastAPI(title="AVA OLO Emergency Service", version="v3.5.40-emergency")

@app.get("/")
async def root():
    """Root endpoint"""
    return HTMLResponse("""
    <html>
    <body>
        <h1>AVA OLO Agricultural Core - Emergency Mode</h1>
        <p>Service is running in emergency minimal mode.</p>
        <p>Version: v3.5.40-emergency</p>
        <p>Status: OPERATIONAL</p>
    </body>
    </html>
    """)

@app.get("/health")
async def health():
    """Health check for ALB"""
    return {
        "status": "healthy",
        "version": "v3.5.40-emergency",
        "service": "agricultural-core-emergency"
    }

@app.get("/api/status")
async def status():
    """API status"""
    return {
        "status": "emergency_mode",
        "message": "Service running with minimal functionality",
        "deployment_issue": "External dependencies causing failures",
        "action": "Diagnosing deployment pipeline"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)