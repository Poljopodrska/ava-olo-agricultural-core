#!/usr/bin/env python3
"""
AVA OLO Dashboard System - Deployment Script
Starts monitoring API, explorer API, and serves dashboard HTML files
"""

import asyncio
import logging
import signal
import sys
import os
import threading
import time
from pathlib import Path
import subprocess
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import TCPServer
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DashboardHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Custom HTTP request handler for serving dashboard files"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)
    
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()
    
    def log_message(self, format, *args):
        # Reduce log noise
        pass

class DashboardSystem:
    """Main dashboard system orchestrator"""
    
    def __init__(self):
        self.monitoring_process = None
        self.explorer_process = None
        self.http_server = None
        self.http_thread = None
        self.running = False
        
        # Configuration
        self.monitoring_port = 8000
        self.explorer_port = 8001
        self.dashboard_port = 8080
        
        self.project_dir = Path(__file__).parent
        
    def start_monitoring_api(self):
        """Start the monitoring API server"""
        try:
            logger.info(f"Starting Monitoring API on port {self.monitoring_port}...")
            
            # Use uvicorn programmatically
            config = uvicorn.Config(
                "monitoring_api:app",
                host="0.0.0.0",
                port=self.monitoring_port,
                log_level="info",
                access_log=False
            )
            
            server = uvicorn.Server(config)
            
            def run_server():
                asyncio.run(server.serve())
            
            self.monitoring_process = threading.Thread(target=run_server, daemon=True)
            self.monitoring_process.start()
            
            logger.info(f"✅ Monitoring API started on http://localhost:{self.monitoring_port}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start Monitoring API: {e}")
            return False
    
    def start_explorer_api(self):
        """Start the database explorer API server"""
        try:
            logger.info(f"Starting Database Explorer API on port {self.explorer_port}...")
            
            config = uvicorn.Config(
                "explorer_api:app",
                host="0.0.0.0",
                port=self.explorer_port,
                log_level="info",
                access_log=False
            )
            
            server = uvicorn.Server(config)
            
            def run_server():
                asyncio.run(server.serve())
            
            self.explorer_process = threading.Thread(target=run_server, daemon=True)
            self.explorer_process.start()
            
            logger.info(f"✅ Database Explorer API started on http://localhost:{self.explorer_port}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start Database Explorer API: {e}")
            return False
    
    def start_dashboard_server(self):
        """Start the dashboard HTML server"""
        try:
            logger.info(f"Starting Dashboard HTTP Server on port {self.dashboard_port}...")
            
            self.http_server = HTTPServer(
                ("", self.dashboard_port), 
                DashboardHTTPRequestHandler
            )
            
            def run_server():
                self.http_server.serve_forever()
            
            self.http_thread = threading.Thread(target=run_server, daemon=True)
            self.http_thread.start()
            
            logger.info(f"✅ Dashboard HTTP Server started on http://localhost:{self.dashboard_port}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start Dashboard HTTP Server: {e}")
            return False
    
    def check_dependencies(self):
        """Check if all required dependencies are available"""
        logger.info("Checking dependencies...")
        
        try:
            import fastapi
            import uvicorn
            import sqlalchemy
            import pandas
            import openpyxl
            logger.info("✅ All required Python packages are available")
        except ImportError as e:
            logger.error(f"❌ Missing required package: {e}")
            logger.error("Please run: pip install -r requirements.txt")
            return False
        
        # Check if database configuration exists
        try:
            from config import DATABASE_URL
            logger.info("✅ Database configuration found")
        except ImportError:
            logger.error("❌ Database configuration not found")
            logger.error("Please ensure config.py exists with proper DATABASE_URL")
            return False
        
        return True
    
    def wait_for_apis(self):
        """Wait for APIs to be ready"""
        import requests
        
        apis = [
            (f"http://localhost:{self.monitoring_port}/health", "Monitoring API"),
            (f"http://localhost:{self.explorer_port}/health", "Explorer API")
        ]
        
        logger.info("Waiting for APIs to be ready...")
        
        for url, name in apis:
            for attempt in range(30):  # 30 seconds timeout
                try:
                    response = requests.get(url, timeout=2)
                    if response.status_code == 200:
                        logger.info(f"✅ {name} is ready")
                        break
                except:
                    time.sleep(1)
            else:
                logger.warning(f"⚠️  {name} may not be fully ready")
    
    def open_dashboards(self):
        """Open dashboard URLs in browser"""
        urls = [
            (f"http://localhost:{self.dashboard_port}/monitoring_dashboard.html", "Monitoring Dashboard"),
            (f"http://localhost:{self.dashboard_port}/database_explorer.html", "Database Explorer")
        ]
        
        logger.info("Opening dashboards in browser...")
        
        for url, name in urls:
            try:
                webbrowser.open(url)
                logger.info(f"🌐 Opened {name}: {url}")
            except Exception as e:
                logger.warning(f"Could not auto-open {name}: {e}")
                logger.info(f"Manual access: {url}")
    
    def display_status(self):
        """Display system status and URLs"""
        print("\n" + "=" * 60)
        print("🌾 AVA OLO Dashboard System - RUNNING")
        print("=" * 60)
        print(f"📊 Monitoring Dashboard:  http://localhost:{self.dashboard_port}/monitoring_dashboard.html")
        print(f"🗃️  Database Explorer:     http://localhost:{self.dashboard_port}/database_explorer.html")
        print(f"🔌 Monitoring API:        http://localhost:{self.monitoring_port}/docs")
        print(f"🔍 Explorer API:          http://localhost:{self.explorer_port}/docs")
        print("=" * 60)
        print("📝 Features Available:")
        print("   • Real-time farmer and field monitoring")
        print("   • Croatian agricultural data visualization")
        print("   • Interactive database exploration")
        print("   • Excel/CSV data export")
        print("   • Live activity feed with WebSocket")
        print("   • Growth trend analysis and projections")
        print("=" * 60)
        print("🛑 Press Ctrl+C to stop all services")
        print("=" * 60)
    
    def start(self):
        """Start the complete dashboard system"""
        logger.info("🚀 Starting AVA OLO Dashboard System...")
        
        # Check dependencies first
        if not self.check_dependencies():
            sys.exit(1)
        
        # Start all services
        success = True
        success &= self.start_monitoring_api()
        success &= self.start_explorer_api()
        success &= self.start_dashboard_server()
        
        if not success:
            logger.error("❌ Failed to start some services")
            sys.exit(1)
        
        # Wait for APIs to be ready
        self.wait_for_apis()
        
        # Open dashboards in browser
        self.open_dashboards()
        
        # Display status
        self.display_status()
        
        self.running = True
        
        # Keep the main process running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop all dashboard services"""
        logger.info("🛑 Stopping AVA OLO Dashboard System...")
        
        self.running = False
        
        # Stop HTTP server
        if self.http_server:
            self.http_server.shutdown()
            logger.info("✅ Dashboard HTTP Server stopped")
        
        logger.info("✅ All services stopped")
        sys.exit(0)

def signal_handler(signum, frame):
    """Handle system signals for graceful shutdown"""
    logger.info("Received shutdown signal")
    dashboard_system.stop()

# Global dashboard system instance
dashboard_system = DashboardSystem()

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Main entry point"""
    print("""
    🌾 AVA OLO Dashboard System
    Croatian Agricultural Virtual Assistant
    
    Starting complete dashboard system with:
    • Real-time monitoring dashboard
    • Interactive database explorer
    • REST APIs with Croatian data
    • WebSocket live updates
    """)
    
    dashboard_system.start()

if __name__ == "__main__":
    main()