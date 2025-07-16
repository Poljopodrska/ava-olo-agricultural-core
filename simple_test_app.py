#!/usr/bin/env python3
print("🚀 SIMPLE APP STARTING...")

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
    print("🚀 Starting uvicorn...")
    uvicorn.run(app, host="0.0.0.0", port=8080)

print("✅ SIMPLE APP SETUP COMPLETE")