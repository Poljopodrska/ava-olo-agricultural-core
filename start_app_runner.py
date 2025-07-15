#!/usr/bin/env python3
"""
🏛️ App Runner Startup Script
Runs both main API and CAVA service in the same container
"""
import os
import sys
import subprocess
import time
import signal
import logging
from threading import Thread

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Process holders
cava_process = None
main_process = None

def signal_handler(sig, frame):
    """Handle shutdown gracefully"""
    logger.info("Shutting down services...")
    if cava_process:
        cava_process.terminate()
    if main_process:
        main_process.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def start_cava_service():
    """Start CAVA service on port 8001"""
    global cava_process
    logger.info("🏛️ Starting CAVA service on port 8001...")
    
    env = os.environ.copy()
    env['PORT'] = '8001'
    
    cava_process = subprocess.Popen(
        [sys.executable, 'implementation/cava/cava_api.py'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    
    # Monitor CAVA output
    for line in cava_process.stdout:
        logger.info(f"[CAVA] {line.strip()}")

def start_main_api():
    """Start main API on port 8080"""
    global main_process
    
    # Wait for CAVA to be ready
    logger.info("⏳ Waiting for CAVA to be ready...")
    for i in range(30):
        try:
            import requests
            response = requests.get('http://localhost:8001/health', timeout=1)
            if response.status_code == 200:
                logger.info("✅ CAVA is ready!")
                break
        except:
            pass
        time.sleep(1)
    
    logger.info("🚀 Starting main API on port 8080...")
    
    # Use the PORT env var from App Runner, default to 8080
    port = os.getenv('PORT', '8080')
    
    main_process = subprocess.Popen(
        [
            'uvicorn',
            'api_gateway_simple:app',
            '--host', '0.0.0.0',
            '--port', port
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    
    # Monitor main API output
    for line in main_process.stdout:
        logger.info(f"[MAIN] {line.strip()}")

def main():
    """Run both services"""
    logger.info("🏛️ AVA OLO Agricultural Core with CAVA")
    logger.info("=" * 50)
    
    # Start CAVA in a thread
    cava_thread = Thread(target=start_cava_service, daemon=True)
    cava_thread.start()
    
    # Give CAVA time to start
    time.sleep(3)
    
    # Start main API (this will block)
    start_main_api()

if __name__ == "__main__":
    main()