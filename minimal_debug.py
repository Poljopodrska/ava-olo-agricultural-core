# minimal_debug.py - Ultra simple version for debugging AWS deployment
from fastapi import FastAPI
import os
import datetime

app = FastAPI()

@app.get("/")
def root():
    return {
        "message": "Minimal debug version working",
        "time": datetime.datetime.now().isoformat(),
        "env_check": {
            "DB_HOST": os.getenv('DB_HOST', 'not_set'),
            "PORT": os.getenv('PORT', '8080')
        }
    }

@app.get("/health/")
def health():
    return {
        "status": "minimal_working",
        "service": "debug_health",
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.get("/api/health")
def api_health():
    return {"status": "healthy", "service": "minimal-debug"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('PORT', '8080'))
    print(f"Starting minimal debug app on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)