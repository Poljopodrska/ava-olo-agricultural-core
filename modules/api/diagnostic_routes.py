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

@router.get("/test-field-activities")
async def test_field_activities_table(farmer: dict = Depends(require_auth)):
    """Test endpoint to check field_activities table structure and accessibility"""
    try:
        results = {}
        
        # Check both tables
        for table_name in ['field_activities', 'tasks']:
            check_table_query = f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = '{table_name}'
            )
            """
            table_result = execute_simple_query(check_table_query, ())
            table_exists = table_result.get('rows')[0][0] if table_result.get('success') and table_result.get('rows') else False
            
            if table_exists:
                # Get table structure
                columns_query = f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
                """
                columns_result = execute_simple_query(columns_query, ())
                
                columns = []
                if columns_result.get('success') and columns_result.get('rows'):
                    for row in columns_result['rows']:
                        columns.append({
                            "name": row[0],
                            "type": row[1],
                            "nullable": row[2],
                            "default": row[3]
                        })
                
                results[table_name] = {
                    "exists": True,
                    "columns": columns
                }
            else:
                results[table_name] = {
                    "exists": False,
                    "columns": []
                }
        
        # Count field activities for this farmer
        if results.get('field_activities', {}).get('exists'):
            count_query = """
            SELECT COUNT(*) 
            FROM field_activities fa
            JOIN fields f ON fa.field_id = f.id
            WHERE f.farmer_id = %s
            """
            count_result = execute_simple_query(count_query, (farmer['farmer_id'],))
            results["activity_count"] = count_result['rows'][0][0] if count_result.get('success') and count_result.get('rows') else 0
            
            # Get recent activities
            recent_query = """
            SELECT fa.id, fa.activity_type, fa.activity_date, f.field_name, fa.product_name
            FROM field_activities fa
            JOIN fields f ON fa.field_id = f.id
            WHERE f.farmer_id = %s
            ORDER BY fa.created_at DESC
            LIMIT 5
            """
            recent_result = execute_simple_query(recent_query, (farmer['farmer_id'],))
            
            if recent_result.get('success') and recent_result.get('rows'):
                results["recent_activities"] = []
                for row in recent_result['rows']:
                    results["recent_activities"].append({
                        "id": row[0],
                        "type": row[1],
                        "date": str(row[2]) if row[2] else None,
                        "field": row[3],
                        "product": row[4]
                    })
            else:
                results["recent_activities"] = []
        
        # Test INSERT capability for field_activities
        test_insert_query = """
        EXPLAIN (ANALYZE false, BUFFERS false, FORMAT TEXT)
        INSERT INTO field_activities (field_id, activity_type, activity_date, product_name, dose_amount, dose_unit, notes, created_by)
        VALUES (1, 'test', '2025-01-01', '', NULL, '', '', 1)
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

@router.get("/test-field-crops")
async def test_field_crops_table(farmer: dict = Depends(require_auth)):
    """Test endpoint to check field_crops table structure"""
    try:
        results = {}
        
        # Check if field_crops table exists
        check_table_query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'field_crops'
        )
        """
        table_result = execute_simple_query(check_table_query, ())
        results["table_exists"] = table_result.get('rows')[0][0] if table_result.get('success') and table_result.get('rows') else False
        
        # Get table structure if it exists
        if results["table_exists"]:
            columns_query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'field_crops'
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
            
            # Count crops for this farmer
            count_query = """
            SELECT COUNT(*) 
            FROM field_crops fc
            JOIN fields f ON fc.field_id = f.id
            WHERE f.farmer_id = %s
            """
            count_result = execute_simple_query(count_query, (farmer['farmer_id'],))
            results["crop_count"] = count_result['rows'][0][0] if count_result.get('success') and count_result.get('rows') else 0
            
            # Get sample data
            sample_query = """
            SELECT fc.*, f.field_name
            FROM field_crops fc
            JOIN fields f ON fc.field_id = f.id
            WHERE f.farmer_id = %s
            ORDER BY fc.id DESC
            LIMIT 3
            """
            sample_result = execute_simple_query(sample_query, (farmer['farmer_id'],))
            
            if sample_result.get('success') and sample_result.get('rows'):
                results["sample_data"] = []
                for row in sample_result['rows']:
                    results["sample_data"].append({
                        "row": str(row)
                    })
        
        return JSONResponse(content={
            "success": True,
            "results": results,
            "farmer_id": farmer['farmer_id']
        })
        
    except Exception as e:
        logger.error(f"Error testing field_crops table: {e}")
        import traceback
        return JSONResponse(content={
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)

@router.post("/test-crop-update")
async def test_crop_update(request: Request, farmer: dict = Depends(require_auth)):
    """Simple test endpoint to debug crop update issues"""
    try:
        # Get request data
        data = await request.json()
        field_id = data.get('field_id')
        
        results = {
            "request_data": data,
            "farmer_id": farmer.get('farmer_id'),
            "field_id": field_id
        }
        
        # Test 1: Check if field exists and belongs to farmer
        field_check = execute_simple_query(
            "SELECT id, field_name FROM fields WHERE id = %s AND farmer_id = %s",
            (int(field_id), farmer['farmer_id'])
        )
        results["field_check"] = {
            "success": field_check.get('success'),
            "found": bool(field_check.get('rows')),
            "error": field_check.get('error')
        }
        
        # Test 2: Check field_crops table structure
        columns_check = execute_simple_query(
            """SELECT column_name, data_type 
               FROM information_schema.columns 
               WHERE table_name = 'field_crops'
               ORDER BY ordinal_position""",
            ()
        )
        if columns_check.get('success') and columns_check.get('rows'):
            results["field_crops_columns"] = [
                f"{row[0]} ({row[1]})" for row in columns_check['rows']
            ]
        
        # Test 3: Try a simple INSERT with minimal data
        test_insert = execute_simple_query(
            """INSERT INTO field_crops (field_id, crop_type, variety) 
               VALUES (%s, 'TEST_CROP', 'TEST_VARIETY')
               RETURNING id""",
            (int(field_id),)
        )
        
        if test_insert.get('success') and test_insert.get('rows'):
            test_id = test_insert['rows'][0][0]
            results["test_insert"] = {"success": True, "id": test_id}
            
            # Clean up test insert
            execute_simple_query("DELETE FROM field_crops WHERE id = %s", (test_id,))
        else:
            results["test_insert"] = {
                "success": False,
                "error": test_insert.get('error')
            }
        
        # Test 4: Check what's currently in field_crops for this field
        current_crops = execute_simple_query(
            "SELECT * FROM field_crops WHERE field_id = %s ORDER BY id DESC LIMIT 1",
            (int(field_id),)
        )
        if current_crops.get('success') and current_crops.get('rows'):
            results["current_crop"] = str(current_crops['rows'][0])
        else:
            results["current_crop"] = "No existing crop entry"
        
        return JSONResponse(content={
            "success": True,
            "tests": results
        })
        
    except Exception as e:
        import traceback
        return JSONResponse(content={
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)

@router.get("/test-chat-messages")
async def test_chat_messages_table(farmer: dict = Depends(require_auth)):
    """Test chat_messages table structure and data"""
    try:
        results = {}
        
        # Check table structure
        columns_query = """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'chat_messages'
        ORDER BY ordinal_position
        """
        columns_result = execute_simple_query(columns_query, ())
        
        if columns_result.get('success') and columns_result.get('rows'):
            results["columns"] = [f"{row[0]} ({row[1]})" for row in columns_result['rows']]
        else:
            results["columns"] = "Table not found or no columns"
        
        # Check for messages with different phone formats
        farmer_id = farmer.get('farmer_id')
        test_formats = [
            f"+farmer_{farmer_id}",
            f"farmer_{farmer_id}",
            f"+{farmer_id}"
        ]
        
        for format in test_formats:
            count_query = "SELECT COUNT(*) FROM chat_messages WHERE wa_phone_number = %s"
            count_result = execute_simple_query(count_query, (format,))
            if count_result.get('success') and count_result.get('rows'):
                count = count_result['rows'][0][0]
                if count > 0:
                    key_name = f"messages_with_{format}".replace("+", "plus_").replace(" ", "_")
                    results[key_name] = count
        
        # Get all unique phone formats in the table
        unique_query = "SELECT DISTINCT wa_phone_number FROM chat_messages LIMIT 10"
        unique_result = execute_simple_query(unique_query, ())
        if unique_result.get('success') and unique_result.get('rows'):
            results["sample_phone_formats"] = [row[0] for row in unique_result['rows']]
        
        # Get latest message for debugging
        latest_query = """
        SELECT wa_phone_number, role, content, timestamp
        FROM chat_messages
        ORDER BY timestamp DESC
        LIMIT 3
        """
        latest_result = execute_simple_query(latest_query, ())
        if latest_result.get('success') and latest_result.get('rows'):
            results["latest_messages"] = []
            for row in latest_result['rows']:
                results["latest_messages"].append({
                    "phone": row[0],
                    "role": row[1],
                    "content": row[2][:50] if row[2] else None,
                    "time": str(row[3]) if row[3] else None
                })
        
        return JSONResponse(content={
            "success": True,
            "farmer_id": farmer_id,
            "expected_format": f"+farmer_{farmer_id}",
            "results": results
        })
        
    except Exception as e:
        import traceback
        return JSONResponse(content={
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)
