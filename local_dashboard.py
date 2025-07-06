#!/usr/bin/env python3
"""
AVA OLO Local Dashboard - Accessible via 127.0.0.1
Simple single-file dashboard that works with minimal setup
"""

import json
import os
import sys
import threading
import time
import webbrowser
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the dashboard"""
    
    def do_GET(self):
        """Handle GET requests"""
        path = self.path.split('?')[0]  # Remove query parameters
        
        if path == '/' or path == '/index.html':
            self.serve_homepage()
        elif path == '/dashboard':
            self.serve_dashboard()
        elif path == '/api/stats':
            self.serve_api_stats()
        elif path == '/api/tables':
            self.serve_api_tables()
        else:
            self.send_error(404, "Page not found")
    
    def serve_homepage(self):
        """Serve the main homepage"""
        html = """<!DOCTYPE html>
<html lang="hr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AVA OLO Dashboard - Hrvatski Poljoprivredni Asistent</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #333;
        }
        .container {
            background: rgba(255, 255, 255, 0.95);
            padding: 3rem;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            max-width: 800px;
            width: 90%;
            text-align: center;
        }
        .logo { font-size: 4rem; margin-bottom: 1rem; }
        h1 { color: #2c5530; font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem; }
        .subtitle { color: #6b7280; font-size: 1.2rem; margin-bottom: 2rem; }
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            margin-bottom: 2rem;
        }
        .dashboard-card {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            text-decoration: none;
            transition: transform 0.3s ease;
            cursor: pointer;
        }
        .dashboard-card:hover { transform: translateY(-5px); }
        .card-icon { font-size: 3rem; margin-bottom: 1rem; }
        .card-title { font-size: 1.5rem; font-weight: 600; margin-bottom: 0.5rem; }
        .card-description { font-size: 1rem; opacity: 0.9; }
        .status { 
            background: rgba(34, 197, 94, 0.1);
            color: #16a34a;
            padding: 1rem;
            border-radius: 10px;
            margin-top: 2rem;
            font-weight: 600;
        }
        @media (max-width: 768px) {
            .dashboard-grid { grid-template-columns: 1fr; }
            .container { padding: 2rem; }
            h1 { font-size: 2rem; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🌾</div>
        <h1>AVA OLO Dashboard</h1>
        <p class="subtitle">Hrvatski Poljoprivredni Virtualni Asistent</p>

        <div class="dashboard-grid">
            <div class="dashboard-card" onclick="window.location.href='/dashboard'">
                <div class="card-icon">📊</div>
                <div class="card-title">Monitoring Dashboard</div>
                <div class="card-description">Praćenje farmi, polja i razgovora u realnom vremenu</div>
            </div>

            <div class="dashboard-card" onclick="showTables()">
                <div class="card-icon">🗃️</div>
                <div class="card-title">Database Explorer</div>
                <div class="card-description">Pregled podataka hrvatskih poljoprivrednika</div>
            </div>
        </div>

        <div class="status">
            ✅ AVA OLO Sistem Aktivan - Pristup: http://127.0.0.1:8088
        </div>
    </div>

    <script>
        function showTables() {
            alert('Database Explorer: Prikazuje tablice sa hrvatskim poljoprivrednim podacima\\n\\n• ava_farmers (147 farmi)\\n• ava_fields (312 polja)\\n• ava_conversations (1,250 razgovora)\\n• farm_tasks (poljoprivredni zadaci)');
        }
    </script>
</body>
</html>"""
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_dashboard(self):
        """Serve the main dashboard page"""
        html = """<!DOCTYPE html>
<html lang="hr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AVA OLO - Monitoring Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        .header {
            background: rgba(255, 255, 255, 0.95);
            padding: 1rem 2rem;
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .logo { display: flex; align-items: center; gap: 1rem; }
        .logo h1 { color: #2c5530; font-size: 1.8rem; font-weight: 700; }
        .dashboard { padding: 2rem; max-width: 1400px; margin: 0 auto; }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        .metric-card {
            background: rgba(255, 255, 255, 0.95);
            padding: 1.5rem;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            transition: transform 0.3s ease;
        }
        .metric-card:hover { transform: translateY(-5px); }
        .metric-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        .metric-title {
            font-size: 0.9rem;
            color: #6b7280;
            font-weight: 600;
            text-transform: uppercase;
        }
        .metric-icon {
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            background: linear-gradient(135deg, #60a5fa, #3b82f6);
        }
        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: #1f2937;
            margin-bottom: 0.5rem;
        }
        .metric-change {
            font-size: 0.9rem;
            font-weight: 600;
            color: #16a34a;
        }
        .chart-card {
            background: rgba(255, 255, 255, 0.95);
            padding: 1.5rem;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }
        .chart-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 1rem;
        }
        .chart-container { position: relative; height: 300px; }
        .activity-feed {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .activity-header {
            padding: 1.5rem;
            border-bottom: 1px solid rgba(0,0,0,0.1);
        }
        .activity-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #1f2937;
        }
        .activity-item {
            padding: 1rem 1.5rem;
            border-bottom: 1px solid rgba(0,0,0,0.05);
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        .activity-icon {
            width: 35px;
            height: 35px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1rem;
            color: white;
            background: #8b5cf6;
        }
        .activity-content { flex: 1; }
        .activity-description {
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 0.25rem;
        }
        .activity-meta { font-size: 0.8rem; color: #6b7280; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">
            <div style="font-size: 2rem;">🌾</div>
            <h1>AVA OLO Dashboard</h1>
        </div>
        <div style="color: #16a34a; font-weight: 600;">
            ✅ Aktivno - 127.0.0.1:8088
        </div>
    </div>

    <div class="dashboard">
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-header">
                    <div class="metric-title">Ukupno Farmi</div>
                    <div class="metric-icon">👨‍🌾</div>
                </div>
                <div class="metric-value" id="totalFarmers">147</div>
                <div class="metric-change">📈 +3 danas</div>
            </div>

            <div class="metric-card">
                <div class="metric-header">
                    <div class="metric-title">Aktivna Polja</div>
                    <div class="metric-icon">🌿</div>
                </div>
                <div class="metric-value" id="totalFields">312</div>
                <div class="metric-change">📈 +7 danas</div>
            </div>

            <div class="metric-card">
                <div class="metric-header">
                    <div class="metric-title">Aktivni Usjevi</div>
                    <div class="metric-icon">🌽</div>
                </div>
                <div class="metric-value" id="activeCrops">89</div>
                <div class="metric-change">📈 +12 danas</div>
            </div>

            <div class="metric-card">
                <div class="metric-header">
                    <div class="metric-title">Razgovori</div>
                    <div class="metric-icon">💬</div>
                </div>
                <div class="metric-value" id="totalConversations">1,250</div>
                <div class="metric-change">📈 +45 danas</div>
            </div>
        </div>

        <div class="chart-card">
            <div class="chart-title">Distribucija Usjeva po Tipovima</div>
            <div class="chart-container">
                <canvas id="cropChart"></canvas>
            </div>
        </div>

        <div class="activity-feed">
            <div class="activity-header">
                <div class="activity-title">Najnovije Aktivnosti</div>
            </div>
            <div class="activity-item">
                <div class="activity-icon">💬</div>
                <div class="activity-content">
                    <div class="activity-description">Nova poruka: pest_control</div>
                    <div class="activity-meta">Marko Horvat • Zagreb • 5 min</div>
                </div>
            </div>
            <div class="activity-item">
                <div class="activity-icon">🌿</div>
                <div class="activity-content">
                    <div class="activity-description">Novo polje: Polje 1 (15.5ha)</div>
                    <div class="activity-meta">Ana Novak • Osijek • 15 min</div>
                </div>
            </div>
            <div class="activity-item">
                <div class="activity-icon">📋</div>
                <div class="activity-content">
                    <div class="activity-description">Zadatak: planting - Kukuruz</div>
                    <div class="activity-meta">Ivo Petrović • Split • 25 min</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Initialize chart
        const ctx = document.getElementById('cropChart').getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Kukuruz', 'Pšenica', 'Suncokret', 'Soja', 'Ječam'],
                datasets: [{
                    data: [1250.5, 890.2, 307.1, 198.7, 156.3],
                    backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444'],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });

        // Update metrics periodically
        async function updateMetrics() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();
                
                document.getElementById('totalFarmers').textContent = data.total_farmers;
                document.getElementById('totalFields').textContent = data.total_fields;
                document.getElementById('activeCrops').textContent = data.active_crops;
                document.getElementById('totalConversations').textContent = data.total_conversations.toLocaleString();
            } catch (error) {
                console.log('Using mock data');
            }
        }

        // Update every 30 seconds
        updateMetrics();
        setInterval(updateMetrics, 30000);
    </script>
</body>
</html>"""
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def serve_api_stats(self):
        """Serve API statistics"""
        stats = {
            "total_farmers": 147,
            "total_fields": 312,
            "active_crops": 89,
            "total_conversations": 1250,
            "new_farmers_24h": 3,
            "new_fields_24h": 7,
            "growth_rate": 12.5,
            "timestamp": datetime.now().isoformat()
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(stats).encode('utf-8'))
    
    def serve_api_tables(self):
        """Serve table information"""
        tables = [
            {
                "name": "ava_farmers",
                "rows": 147,
                "description": "Hrvatski poljoprivrednici registrirani u sustavu",
                "sample_data": [
                    ["Marko Horvat", "Zagreb", "grain", "50.5 ha"],
                    ["Ana Novak", "Osijek", "mixed", "25.0 ha"],
                    ["Ivo Petrović", "Split", "vegetable", "15.2 ha"]
                ]
            },
            {
                "name": "ava_fields",
                "rows": 312,
                "description": "Poljoprivredna polja u vlasništvu farmi",
                "sample_data": [
                    ["Polje 1", "15.5 ha", "clay soil"],
                    ["Glavno polje", "28.2 ha", "loam soil"],
                    ["Sjeverno polje", "12.8 ha", "sandy soil"]
                ]
            },
            {
                "name": "ava_conversations",
                "rows": 1250,
                "description": "Razgovori s poljoprivrednicima putem AVA sustava",
                "sample_data": [
                    ["pest_control", "5 min ago", "Marko Horvat"],
                    ["fertilization", "15 min ago", "Ana Novak"],
                    ["weather", "25 min ago", "Ivo Petrović"]
                ]
            }
        ]
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(tables).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

class LocalDashboard:
    """Simple local dashboard system"""
    
    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 8088
        self.server = None
        
    def start(self):
        """Start the dashboard server"""
        print(f"""
🌾 AVA OLO Local Dashboard
═══════════════════════════════════════
Croatian Agricultural Virtual Assistant

🌐 Dashboard URL: http://{self.host}:{self.port}
📊 Monitoring:    http://{self.host}:{self.port}/dashboard
🔍 Database:      http://{self.host}:{self.port}/api/tables

Starting server on {self.host}:{self.port}...
        """)
        
        # Start server
        self.server = HTTPServer((self.host, self.port), DashboardHandler)
        
        # Open browser after delay
        def open_browser():
            time.sleep(2)
            try:
                webbrowser.open(f'http://{self.host}:{self.port}')
                print(f"✅ Opened browser: http://{self.host}:{self.port}")
            except:
                print(f"📱 Manual access: http://{self.host}:{self.port}")
        
        threading.Thread(target=open_browser, daemon=True).start()
        
        # Start serving
        print(f"✅ Server running on http://{self.host}:{self.port}")
        print("🛑 Press Ctrl+C to stop")
        print("═" * 50)
        
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Dashboard stopped")
            self.server.shutdown()

def main():
    dashboard = LocalDashboard()
    dashboard.start()

if __name__ == "__main__":
    main()