#!/usr/bin/env python3
"""
Diagnostic routes for testing IP detection and language
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import httpx
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/diagnostic", tags=["diagnostic"])

@router.get("/ip-check", response_class=HTMLResponse)
async def check_ip_detection(request: Request):
    """Show what IP and country is being detected"""
    
    # Get all possible IP headers
    x_forwarded_for = request.headers.get("X-Forwarded-For", "Not present")
    x_real_ip = request.headers.get("X-Real-IP", "Not present")
    cf_connecting_ip = request.headers.get("CF-Connecting-IP", "Not present")
    x_forwarded = request.headers.get("X-Forwarded", "Not present")
    forwarded = request.headers.get("Forwarded", "Not present")
    
    # Get detected IP using same logic as main app
    client_ip = request.headers.get("X-Forwarded-For")
    if client_ip:
        client_ip = client_ip.split(",")[0].strip()
    else:
        client_ip = request.headers.get("X-Real-IP")
        if not client_ip and request.client:
            client_ip = request.client.host
        elif not client_ip:
            client_ip = "127.0.0.1"
    
    # Try to geolocate
    geo_info = {}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://ip-api.com/json/{client_ip}",
                timeout=5.0
            )
            if response.status_code == 200:
                geo_info = response.json()
    except Exception as e:
        geo_info = {"error": str(e)}
    
    # Check browser language
    accept_language = request.headers.get("Accept-Language", "Not present")
    user_agent = request.headers.get("User-Agent", "Not present")
    
    # Language mapping
    country_to_language = {
        'SI': 'Slovenian (sl)',
        'HR': 'Croatian (hr)',
        'IT': 'Italian (it)',
        'AT': 'German (de)',
        'DE': 'German (de)',
        'GB': 'English (en)',
        'US': 'English (en)',
    }
    
    detected_language = country_to_language.get(
        geo_info.get('countryCode', ''), 
        'English (en) - default'
    )
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>IP Detection Diagnostic</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background: #f5f5f5;
            }}
            .container {{
                background: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #333;
                border-bottom: 2px solid #4CAF50;
                padding-bottom: 10px;
            }}
            .section {{
                margin: 20px 0;
                padding: 15px;
                background: #f9f9f9;
                border-left: 4px solid #4CAF50;
            }}
            .label {{
                font-weight: bold;
                color: #555;
                display: inline-block;
                width: 150px;
            }}
            .value {{
                color: #333;
                font-family: monospace;
            }}
            .detected {{
                background: #e8f5e9;
                padding: 15px;
                border-radius: 4px;
                margin: 20px 0;
                border: 2px solid #4CAF50;
            }}
            .warning {{
                background: #fff3e0;
                padding: 10px;
                border-radius: 4px;
                margin: 10px 0;
                border-left: 4px solid #ff9800;
            }}
            .success {{
                color: #4CAF50;
                font-weight: bold;
            }}
            .error {{
                color: #f44336;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 IP Detection Diagnostic</h1>
            
            <div class="detected">
                <h2>✅ Detected Information</h2>
                <p><span class="label">Your IP:</span> <span class="value success">{client_ip}</span></p>
                <p><span class="label">Country:</span> <span class="value">{geo_info.get('country', 'Unknown')}</span></p>
                <p><span class="label">Country Code:</span> <span class="value">{geo_info.get('countryCode', 'Unknown')}</span></p>
                <p><span class="label">City:</span> <span class="value">{geo_info.get('city', 'Unknown')}</span></p>
                <p><span class="label">Language:</span> <span class="value success">{detected_language}</span></p>
            </div>
            
            <div class="section">
                <h3>📍 Full Geolocation Data</h3>
                <p><span class="label">ISP:</span> <span class="value">{geo_info.get('isp', 'Unknown')}</span></p>
                <p><span class="label">Organization:</span> <span class="value">{geo_info.get('org', 'Unknown')}</span></p>
                <p><span class="label">AS:</span> <span class="value">{geo_info.get('as', 'Unknown')}</span></p>
                <p><span class="label">Region:</span> <span class="value">{geo_info.get('regionName', 'Unknown')}</span></p>
                <p><span class="label">Timezone:</span> <span class="value">{geo_info.get('timezone', 'Unknown')}</span></p>
                <p><span class="label">Coordinates:</span> <span class="value">{geo_info.get('lat', 'Unknown')}, {geo_info.get('lon', 'Unknown')}</span></p>
            </div>
            
            <div class="section">
                <h3>🌐 HTTP Headers</h3>
                <p><span class="label">X-Forwarded-For:</span> <span class="value">{x_forwarded_for}</span></p>
                <p><span class="label">X-Real-IP:</span> <span class="value">{x_real_ip}</span></p>
                <p><span class="label">CF-Connecting-IP:</span> <span class="value">{cf_connecting_ip}</span></p>
                <p><span class="label">Accept-Language:</span> <span class="value">{accept_language}</span></p>
            </div>
            
            <div class="section">
                <h3>📱 Browser Info</h3>
                <p><span class="label">User-Agent:</span></p>
                <p class="value" style="word-break: break-all;">{user_agent}</p>
            </div>
            
            <div class="warning">
                <h3>⚠️ Note about Mobile Roaming</h3>
                <p>If you're using a mobile connection while roaming:</p>
                <ul>
                    <li>Your traffic may be routed through your home country's network</li>
                    <li>This means your IP will appear as your home country, not your current location</li>
                    <li>Try using WiFi for accurate location detection</li>
                    <li>Or use a local SIM card for proper geolocation</li>
                </ul>
            </div>
            
            <div style="margin-top: 30px; text-align: center;">
                <a href="/" style="background: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">← Back to Home</a>
            </div>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)