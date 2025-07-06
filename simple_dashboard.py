#!/usr/bin/env python3
"""
AVA OLO Simple Dashboard - Works with minimal dependencies
Launches a basic dashboard system without requiring pandas/openpyxl
"""

import asyncio
import json
import logging
import os
import sys
import threading
import time
import webbrowser
from datetime import datetime, timedelta
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Dict, Any, List

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Simple monitoring API
monitoring_app = FastAPI(title="AVA OLO Monitoring API (Simple)", version="1.0.0")

monitoring_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data for demonstration
mock_data = {
    "total_farmers": 147,
    "total_fields": 312,
    "active_crops": 89,
    "total_conversations": 1250,
    "new_farmers_24h": 3,
    "new_fields_24h": 7,
    "growth_rate": 12.5
}

@monitoring_app.get("/api/stats/overview")
async def get_overview():
    """Get overview statistics"""
    return {
        "total_farmers": mock_data["total_farmers"],
        "total_fields": mock_data["total_fields"],
        "total_hectares": 2547.8,
        "active_crops": mock_data["active_crops"],
        "total_conversations": mock_data["total_conversations"],
        "hectares_by_crop": {
            "Kukuruz": 1250.5,
            "Pšenica": 890.2,
            "Suncokret": 307.1
        },
        "farmers_by_type": {
            "grain": 87,
            "vegetable": 34,
            "mixed": 26
        },
        "farmers_by_city": {
            "Zagreb": 45,
            "Osijek": 32,
            "Split": 28,
            "Rijeka": 18
        }
    }

@monitoring_app.get("/api/stats/growth-trends")
async def get_growth_trends():
    """Get growth trends"""
    return {
        "new_farmers_24h": mock_data["new_farmers_24h"],
        "new_farmers_7d": 18,
        "new_farmers_30d": 67,
        "new_fields_24h": mock_data["new_fields_24h"],
        "new_fields_7d": 42,
        "new_fields_30d": 156,
        "growth_rate_daily": mock_data["growth_rate"],
        "growth_rate_weekly": 8.7
    }

@monitoring_app.get("/api/stats/activity-today")
async def get_activity_today():
    """Get today's activity"""
    return {
        "new_fields": mock_data["new_fields_24h"],
        "new_crops": 12,
        "new_tasks": 23,
        "new_conversations": 45,
        "active_farmers": 34,
        "total_activity": 127
    }

@monitoring_app.get("/api/stats/growth-chart")
async def get_growth_chart():
    """Get growth chart data"""
    base_date = datetime.now()
    data = []
    
    for i in range(30):
        date = base_date - timedelta(days=29-i)
        data.append({
            "date": date.strftime("%Y-%m-%d"),
            "cumulative_farmers": 120 + i * 2,
            "new_farmers": 2 if i % 3 == 0 else 1,
            "cumulative_fields": 250 + i * 3,
            "new_fields": 3 if i % 2 == 0 else 2
        })
    
    return data

@monitoring_app.get("/api/activity/live-feed")
async def get_live_feed():
    """Get live activity feed"""
    activities = [
        {
            "id": 1,
            "table_name": "ava_conversations",
            "activity_type": "conversation",
            "description": "Nova poruka: pest_control",
            "farmer_name": "Marko Horvat",
            "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(),
            "details": {"topic": "pest_control"}
        },
        {
            "id": 2,
            "table_name": "ava_fields",
            "activity_type": "field_created",
            "description": "Novo polje: Polje 1 (15.5ha)",
            "farmer_name": "Ana Novak",
            "timestamp": (datetime.now() - timedelta(minutes=15)).isoformat(),
            "details": {"field_name": "Polje 1", "field_size": 15.5}
        },
        {
            "id": 3,
            "table_name": "farm_tasks",
            "activity_type": "task_logged",
            "description": "Zadatak: planting",
            "farmer_name": "Ivo Petrović",
            "timestamp": (datetime.now() - timedelta(minutes=25)).isoformat(),
            "details": {"task_type": "planting"}
        }
    ]
    
    return activities

@monitoring_app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "timestamp": datetime.now().isoformat()
    }

# Simple database explorer API
explorer_app = FastAPI(title="AVA OLO Explorer API (Simple)", version="1.0.0")

explorer_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@explorer_app.get("/api/schema/tables")
async def get_tables():
    """Get table information"""
    return [
        {
            "name": "ava_farmers",
            "row_count": 147,
            "columns": [
                {"name": "id", "type": "integer", "nullable": False},
                {"name": "farm_name", "type": "varchar", "nullable": True},
                {"name": "manager_name", "type": "varchar", "nullable": True},
                {"name": "city", "type": "varchar", "nullable": True}
            ],
            "foreign_keys": [],
            "description": "Croatian farmers registered in the system"
        },
        {
            "name": "ava_fields",
            "row_count": 312,
            "columns": [
                {"name": "field_id", "type": "integer", "nullable": False},
                {"name": "farmer_id", "type": "integer", "nullable": False},
                {"name": "field_name", "type": "varchar", "nullable": False},
                {"name": "field_size", "type": "decimal", "nullable": True}
            ],
            "foreign_keys": [
                {"constrained_columns": ["farmer_id"], "referred_table": "ava_farmers", "referred_columns": ["id"]}
            ],
            "description": "Agricultural fields owned by farmers"
        },
        {
            "name": "ava_conversations",
            "row_count": 1250,
            "columns": [
                {"name": "id", "type": "integer", "nullable": False},
                {"name": "farmer_id", "type": "integer", "nullable": True},
                {"name": "question", "type": "text", "nullable": False},
                {"name": "answer", "type": "text", "nullable": False},
                {"name": "topic", "type": "varchar", "nullable": True}
            ],
            "foreign_keys": [
                {"constrained_columns": ["farmer_id"], "referred_table": "ava_farmers", "referred_columns": ["id"]}
            ],
            "description": "Chat conversations with farmers"
        }
    ]

@explorer_app.get("/api/schema/relationships")
async def get_relationships():
    """Get table relationships"""
    return [
        {
            "from_table": "ava_fields",
            "from_column": "farmer_id",
            "to_table": "ava_farmers",
            "to_column": "id",
            "relationship_type": "foreign_key"
        },
        {
            "from_table": "ava_conversations",
            "from_column": "farmer_id",
            "to_table": "ava_farmers",
            "to_column": "id",
            "relationship_type": "foreign_key"
        }
    ]

@explorer_app.get("/api/data/ava_farmers")
async def get_farmers_data():
    """Get farmers table data"""
    return {
        "table_name": "ava_farmers",
        "columns": ["id", "farm_name", "manager_name", "manager_last_name", "city", "farmer_type"],
        "rows": [
            ["1", "Farma Horvat", "Marko", "Horvat", "Zagreb", "grain"],
            ["2", "OPG Novak", "Ana", "Novak", "Osijek", "mixed"],
            ["3", "Farma Petrović", "Ivo", "Petrović", "Split", "vegetable"],
            ["4", "Gospodarstvo Babić", "Maja", "Babić", "Rijeka", "grain"],
            ["5", "OPG Jurić", "Tomislav", "Jurić", "Zadar", "mixed"]
        ],
        "total_count": 147,
        "page": 1,
        "limit": 50,
        "has_more": True
    }

@explorer_app.get("/health")
async def explorer_health():
    """Explorer health check"""
    return {
        "status": "healthy",
        "tables": 8,
        "timestamp": datetime.now().isoformat()
    }

# HTTP Server for dashboard files
class DashboardHTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)
    
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()
    
    def log_message(self, format, *args):
        pass  # Reduce log noise

class SimpleDashboardSystem:
    """Simple dashboard system launcher"""
    
    def __init__(self):
        self.monitoring_port = 8010
        self.explorer_port = 8011
        self.dashboard_port = 8090
        self.running = False
    
    def start_monitoring_api(self):
        """Start monitoring API"""
        def run():
            config = uvicorn.Config(
                monitoring_app,
                host="0.0.0.0",
                port=self.monitoring_port,
                log_level="error"
            )
            server = uvicorn.Server(config)
            asyncio.run(server.serve())
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        logger.info(f"✅ Monitoring API started on port {self.monitoring_port}")
    
    def start_explorer_api(self):
        """Start explorer API"""
        def run():
            config = uvicorn.Config(
                explorer_app,
                host="0.0.0.0",
                port=self.explorer_port,
                log_level="error"
            )
            server = uvicorn.Server(config)
            asyncio.run(server.serve())
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        logger.info(f"✅ Explorer API started on port {self.explorer_port}")
    
    def start_dashboard_server(self):
        """Start dashboard HTTP server"""
        def run():
            httpd = HTTPServer(("", self.dashboard_port), DashboardHTTPRequestHandler)
            httpd.serve_forever()
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        logger.info(f"✅ Dashboard server started on port {self.dashboard_port}")
    
    def open_dashboards(self):
        """Open dashboards in browser"""
        time.sleep(3)  # Wait for servers to start
        
        urls = [
            f"http://localhost:{self.dashboard_port}/index.html",
            f"http://localhost:{self.dashboard_port}/monitoring_dashboard.html"
        ]
        
        for url in urls:
            try:
                webbrowser.open(url)
                logger.info(f"🌐 Opened: {url}")
                break  # Open only the first one
            except:
                pass
    
    def display_status(self):
        """Display system status"""
        print("\n" + "=" * 60)
        print("🌾 AVA OLO Simple Dashboard - RUNNING")
        print("=" * 60)
        print(f"🏠 Main Page:           http://localhost:{self.dashboard_port}/index.html")
        print(f"📊 Monitoring:          http://localhost:{self.dashboard_port}/monitoring_dashboard.html")
        print(f"🗃️ Database Explorer:   http://localhost:{self.dashboard_port}/database_explorer.html")
        print(f"🔌 Monitoring API:      http://localhost:{self.monitoring_port}/docs")
        print(f"🔍 Explorer API:        http://localhost:{self.explorer_port}/docs")
        print("=" * 60)
        print("📝 Note: Using mock data for demonstration")
        print("🛑 Press Ctrl+C to stop")
        print("=" * 60)
    
    def start(self):
        """Start the dashboard system"""
        print("""
🌾 AVA OLO Simple Dashboard
Croatian Agricultural Virtual Assistant

Starting system with mock data...
        """)
        
        # Start all services
        self.start_monitoring_api()
        self.start_explorer_api()
        self.start_dashboard_server()
        
        # Open browser
        threading.Thread(target=self.open_dashboards, daemon=True).start()
        
        # Display status
        self.display_status()
        
        # Keep running
        self.running = True
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Dashboard stopped")
            self.running = False

def main():
    dashboard = SimpleDashboardSystem()
    dashboard.start()

if __name__ == "__main__":
    main()