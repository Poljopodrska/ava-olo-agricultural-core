#!/usr/bin/env python3
"""
AVA OLO Agricultural Core - v4.11.8
Add inline endpoints without module imports
"""
import os
import sys
import logging
from datetime import datetime

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Version
VERSION = "v4.11.8"

# Initialize FastAPI
app = FastAPI(
    title="AVA OLO Agricultural Core",
    version=VERSION
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import simple router
try:
    from simple_health_router import router as simple_router
    app.include_router(simple_router)
    logger.info("Simple router included")
except Exception as e:
    logger.error(f"Failed to import simple router: {e}")

# Models
class LoginRequest(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    message: str
    farmer_id: str = "1"

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return JSONResponse(content={
        "message": "AVA OLO Agricultural Core API",
        "version": VERSION,
        "status": "operational",
        "timestamp": datetime.now().isoformat()
    })

# Health endpoint
@app.get("/health")
async def health():
    """Basic health check"""
    return JSONResponse(content={
        "status": "healthy",
        "version": VERSION,
        "timestamp": datetime.now().isoformat()
    })

# API health endpoint
@app.get("/api/v1/health")
async def api_health():
    """API health check"""
    return JSONResponse(content={
        "status": "healthy",
        "version": VERSION,
        "service": "agricultural-core",
        "timestamp": datetime.now().isoformat()
    })

# Auth endpoints
@app.post("/api/v1/auth/login")
async def login(request: LoginRequest):
    """Simple login endpoint"""
    return JSONResponse(content={
        "success": True,
        "token": "test-token-12345",
        "user": {
            "id": 1,
            "username": request.username,
            "role": "farmer"
        }
    })

@app.post("/api/v1/auth/logout")
async def logout():
    """Simple logout endpoint"""
    return JSONResponse(content={"success": True})

# Weather endpoint
@app.get("/api/v1/weather/current")
async def get_weather(location: str = "Sofia"):
    """Get current weather"""
    return JSONResponse(content={
        "location": location,
        "temperature": 22,
        "condition": "Sunny",
        "humidity": 65,
        "wind_speed": 10,
        "timestamp": datetime.now().isoformat()
    })

# Chat endpoint
@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    """Simple chat endpoint"""
    return JSONResponse(content={
        "response": f"I understand you said: {request.message}",
        "farmer_id": request.farmer_id,
        "timestamp": datetime.now().isoformat()
    })

# Farmer dashboard endpoint
@app.get("/farmer/dashboard")
async def farmer_dashboard(request: Request):
    """Farmer dashboard"""
    lang = request.query_params.get("lang", "en")
    translations = {
        "en": {"title": "Farmer Dashboard", "welcome": "Welcome"},
        "bg": {"title": "Фермерско табло", "welcome": "Добре дошли"},
        "sl": {"title": "Kmetijska nadzorna plošča", "welcome": "Dobrodošli"}
    }
    return JSONResponse(content={
        "message": translations.get(lang, translations["en"])["title"],
        "version": VERSION,
        "language": lang,
        "farmer": {"id": 1, "name": "Test Farmer"}
    })

# Task management endpoints
@app.get("/api/v1/tasks")
async def get_tasks(farmer_id: int = 1):
    """Get farmer tasks"""
    return JSONResponse(content={
        "tasks": [
            {"id": 1, "title": "Water crops", "status": "pending"},
            {"id": 2, "title": "Check soil", "status": "completed"}
        ],
        "farmer_id": farmer_id
    })

# Field management endpoints
@app.get("/api/v1/fields")
async def get_fields(farmer_id: int = 1):
    """Get farmer fields"""
    return JSONResponse(content={
        "fields": [
            {"id": 1, "name": "North Field", "size": 10.5, "crop": "wheat"},
            {"id": 2, "name": "South Field", "size": 8.2, "crop": "corn"}
        ],
        "farmer_id": farmer_id
    })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)