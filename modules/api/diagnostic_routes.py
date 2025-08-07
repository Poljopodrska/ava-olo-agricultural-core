#!/usr/bin/env python3
"""
Diagnostic routes for testing IP detection and language
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
import httpx
import logging
from ..core.simple_db import execute_simple_query
from ..auth.routes import require_auth

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

@router.get("/check-field/{field_name}")
async def check_field_by_name(field_name: str, farmer: dict = Depends(require_auth)):
    """Check if a field with given name exists for the current farmer"""
    try:
        farmer_id = farmer.get('farmer_id')
        
        # Search for the field
        query = """
        SELECT id, field_name, farmer_id, area_ha
        FROM fields 
        WHERE farmer_id = %s AND field_name = %s
        ORDER BY id DESC
        """
        result = execute_simple_query(query, (farmer_id, field_name))
        
        if result.get('success') and result.get('rows'):
            fields = []
            for row in result['rows']:
                fields.append({
                    'id': row[0],
                    'field_name': row[1],
                    'farmer_id': row[2],
                    'area_ha': float(row[3]) if row[3] else None
                })
            
            return JSONResponse(content={
                "success": True,
                "found": True,
                "fields": fields,
                "count": len(fields)
            })
        else:
            # Also check without farmer_id filter to see if it exists for another farmer
            query_all = """
            SELECT id, field_name, farmer_id, area_ha
            FROM fields 
            WHERE field_name = %s
            ORDER BY id DESC
            LIMIT 10
            """
            result_all = execute_simple_query(query_all, (field_name,))
            
            other_farmers_fields = []
            if result_all.get('success') and result_all.get('rows'):
                for row in result_all['rows']:
                    other_farmers_fields.append({
                        'id': row[0],
                        'field_name': row[1],
                        'farmer_id': row[2],
                        'area_ha': float(row[3]) if row[3] else None
                    })
            
            return JSONResponse(content={
                "success": True,
                "found": False,
                "message": f"No field named '{field_name}' found for farmer {farmer_id}",
                "fields_for_other_farmers": other_farmers_fields
            })
            
    except Exception as e:
        logger.error(f"Error checking field: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@router.get("/recent-fields")
async def get_recent_fields(farmer: dict = Depends(require_auth)):
    """Get the most recent fields for the current farmer"""
    try:
        farmer_id = farmer.get('farmer_id')
        
        # Get last 10 fields
        query = """
        SELECT id, field_name, farmer_id, area_ha, country, latitude, longitude
        FROM fields 
        WHERE farmer_id = %s
        ORDER BY id DESC
        LIMIT 10
        """
        result = execute_simple_query(query, (farmer_id,))
        
        fields = []
        if result.get('success') and result.get('rows'):
            for row in result['rows']:
                fields.append({
                    'id': row[0],
                    'field_name': row[1],
                    'farmer_id': row[2],
                    'area_ha': float(row[3]) if row[3] else None,
                    'country': row[4],
                    'latitude': float(row[5]) if row[5] else None,
                    'longitude': float(row[6]) if row[6] else None
                })
        
        # Also get total count
        count_query = "SELECT COUNT(*) FROM fields WHERE farmer_id = %s"
        count_result = execute_simple_query(count_query, (farmer_id,))
        total_count = count_result['rows'][0][0] if count_result.get('success') and count_result.get('rows') else 0
        
        return JSONResponse(content={
            "success": True,
            "farmer_id": farmer_id,
            "recent_fields": fields,
            "count": len(fields),
            "total_count": total_count
        })
            
    except Exception as e:
        logger.error(f"Error getting recent fields: {e}")
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@router.get("/all-fields-debug")
async def get_all_fields_debug(farmer: dict = Depends(require_auth)):
    """Debug endpoint to see all fields and why they might not be showing"""
    try:
        farmer_id = farmer.get('farmer_id')
        
        # Get ALL fields for this farmer with full details
        query = """
        SELECT id, field_name, farmer_id, area_ha, country, 
               latitude, longitude, blok_id, raba, notes
        FROM fields 
        WHERE farmer_id = %s
        ORDER BY id DESC
        """
        result = execute_simple_query(query, (farmer_id,))
        
        fields = []
        if result.get('success') and result.get('rows'):
            for row in result['rows']:
                fields.append({
                    'id': row[0],
                    'field_name': row[1],
                    'farmer_id': row[2],
                    'area_ha': float(row[3]) if row[3] else None,
                    'country': row[4],
                    'latitude': float(row[5]) if row[5] else None,
                    'longitude': float(row[6]) if row[6] else None,
                    'blok_id': row[7],
                    'raba': row[8],
                    'notes': row[9]
                })
        
        # Also check what get_farmer_fields returns
        from ..api.farmer_dashboard_routes import get_farmer_fields
        dashboard_fields = get_farmer_fields(farmer_id)
        
        return JSONResponse(content={
            "success": True,
            "farmer_id": farmer_id,
            "direct_query_fields": fields,
            "direct_query_count": len(fields),
            "dashboard_function_fields": dashboard_fields,
            "dashboard_function_count": len(dashboard_fields),
            "mismatch": len(fields) != len(dashboard_fields)
        })
            
    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        import traceback
        return JSONResponse(content={
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)

@router.get("/test-tasks-table")
async def test_tasks_table(farmer: dict = Depends(require_auth)):
    """Test endpoint to check tasks table structure and accessibility"""
    try:
        results = {}
        
        # Check if tasks table exists
        check_table_query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'tasks'
        )
        """
        table_result = execute_simple_query(check_table_query, ())
        results["table_exists"] = table_result.get('rows')[0][0] if table_result.get('success') and table_result.get('rows') else False
        
        # Get table structure if it exists
        if results["table_exists"]:
            columns_query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'tasks'
            ORDER BY ordinal_position
            """
            columns_result = execute_simple_query(columns_query, ())
            
            if columns_result.get('success') and columns_result.get('rows'):
                results["columns"] = []
                for row in columns_result['rows']:
                    results["columns"].append({
                        "name": row[0],
                        "type": row[1],
                        "nullable": row[2],
                        "default": row[3]
                    })
            
            # Count tasks for this farmer
            count_query = """
            SELECT COUNT(*) 
            FROM tasks t
            JOIN fields f ON t.field_id = f.id
            WHERE f.farmer_id = %s
            """
            count_result = execute_simple_query(count_query, (farmer['farmer_id'],))
            results["task_count"] = count_result['rows'][0][0] if count_result.get('success') and count_result.get('rows') else 0
            
            # Get recent tasks
            recent_query = """
            SELECT t.id, t.task_type, t.date_performed, f.field_name
            FROM tasks t
            JOIN fields f ON t.field_id = f.id
            WHERE f.farmer_id = %s
            ORDER BY t.created_at DESC
            LIMIT 5
            """
            recent_result = execute_simple_query(recent_query, (farmer['farmer_id'],))
            
            if recent_result.get('success') and recent_result.get('rows'):
                results["recent_tasks"] = []
                for row in recent_result['rows']:
                    results["recent_tasks"].append({
                        "id": row[0],
                        "type": row[1],
                        "date": str(row[2]) if row[2] else None,
                        "field": row[3]
                    })
            else:
                results["recent_tasks"] = []
        
        # Test INSERT capability
        test_insert_query = """
        EXPLAIN (ANALYZE false, BUFFERS false, FORMAT TEXT)
        INSERT INTO tasks (field_id, task_type, date_performed, material_used, quantity, unit, notes)
        VALUES (1, 'test', '2025-01-01', '', NULL, '', '')
        """
        try:
            insert_test = execute_simple_query(test_insert_query, ())
            results["can_insert"] = insert_test.get('success', False)
            if not insert_test.get('success'):
                results["insert_error"] = insert_test.get('error')
        except Exception as e:
            results["can_insert"] = False
            results["insert_error"] = str(e)
        
        return JSONResponse(content={
            "success": True,
            "results": results,
            "farmer_id": farmer['farmer_id']
        })
        
    except Exception as e:
        logger.error(f"Error testing tasks table: {e}")
        import traceback
        return JSONResponse(content={
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)