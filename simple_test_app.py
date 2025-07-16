#!/usr/bin/env python3
print("🚀 SIMPLE APP STARTING...")

import os
print(f"🚀 Environment PORT: {os.getenv('PORT')}")
print(f"🚀 All env vars: {dict(os.environ)}")

from fastapi import FastAPI
import uvicorn

print("✅ FastAPI imported")

app = FastAPI()

print("✅ FastAPI app created")

@app.get("/")
async def root():
    return {"message": "MINIMAL APP WORKING", "status": "success"}

@app.get("/health")
async def health():
    return {"status": "healthy", "minimal": True}

print("✅ Routes defined")

if __name__ == "__main__":
    # CRITICAL: Use PORT from environment variable
    port = int(os.getenv("PORT", 8080))
    print(f"🚀 Starting uvicorn on port: {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

print("✅ SIMPLE APP SETUP COMPLETE")