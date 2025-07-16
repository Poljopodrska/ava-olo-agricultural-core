"""
Minimal API Gateway for deployment safety testing
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="AVA OLO Agricultural Core API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {
        "status": "healthy",
        "service": "ava-olo-agricultural-core",
        "version": "1.0.0",
        "message": "Service is running correctly"
    }

# Simple query endpoint
@app.post("/api/v1/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process agricultural query"""
    return QueryResponse(
        answer=f"Thank you for your agricultural question: '{request.query}'. This is a test response from the API Gateway.",
        confidence=0.9,
        sources=["Test system"]
    )

# Farmers endpoint
@app.get("/api/v1/farmers")
async def get_farmers():
    """Get farmers list"""
    return {
        "farmers": [
            {"id": 1, "name": "Test Farmer", "farm_name": "Test Farm"}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)