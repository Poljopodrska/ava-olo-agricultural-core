#!/usr/bin/env python3
"""Debug version - minimal server to test deployment"""
import uvicorn
import logging
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "debug server running", "version": "v3.9.13-debug"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    logger.info("Starting debug server on port 8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)