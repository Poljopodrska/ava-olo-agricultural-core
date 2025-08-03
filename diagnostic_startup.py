#!/usr/bin/env python3
"""
Diagnostic startup script to test what's failing
"""
import sys
import os

print("=== DIAGNOSTIC STARTUP ===")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"Environment PORT: {os.environ.get('PORT', 'NOT SET')}")

# Test imports one by one
try:
    print("Testing FastAPI import...")
    from fastapi import FastAPI
    print("✅ FastAPI imported successfully")
except Exception as e:
    print(f"❌ FastAPI import failed: {e}")
    sys.exit(1)

try:
    print("Testing uvicorn import...")
    import uvicorn
    print("✅ uvicorn imported successfully")
except Exception as e:
    print(f"❌ uvicorn import failed: {e}")
    sys.exit(1)

try:
    print("Testing asyncpg import...")
    import asyncpg
    print("✅ asyncpg imported successfully")
except Exception as e:
    print(f"❌ asyncpg import failed: {e}")

# Create minimal app
print("Creating minimal FastAPI app...")
app = FastAPI()

@app.get("/")
async def root():
    return {"status": "diagnostic mode", "python": sys.version}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)