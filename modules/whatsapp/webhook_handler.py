"""
WhatsApp Webhook Handler for Twilio Integration
Handles incoming WhatsApp messages, status callbacks, and fallback scenarios
Now integrated with CAVA chat engine for intelligent responses
"""
from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import Response
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import asyncpg

# CAVA import moved inside functions to avoid circular imports

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/whatsapp", tags=["whatsapp"])

# Get environment variables
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
BASE_URL = os.getenv('BASE_URL', 'http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com')


async def get_or_create_farmer_by_phone(phone_number: str) -> Dict[str, Any]:
    """Get farmer by phone number or create a new one"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            # First try to find farmer by WhatsApp phone
            farmer = await conn.fetchrow("""
                SELECT id, manager_name, farm_name, city 
                FROM farmers 
                WHERE wa_phone_number = $1 OR phone = $1
                LIMIT 1
            """, phone_number)
            
            if farmer:
                logger.info(f"Found existing farmer {farmer['id']} for phone {phone_number}")
                return dict(farmer)
            
            # If not found, create a basic farmer record
            logger.info(f"Creating new farmer for phone {phone_number}")
            new_farmer_id = await conn.fetchval("""
                INSERT INTO farmers (wa_phone_number, phone, manager_name, farm_name, city)
                VALUES ($1, $1, 'WhatsApp User', 'Farm', 'Unknown')
                RETURNING id
            """, phone_number)
            
            return {
                'id': new_farmer_id,
                'manager_name': 'WhatsApp User',
                'farm_name': 'Farm',
                'city': 'Unknown'
            }
            
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"Error getting/creating farmer: {str(e)}")
        # Return a default farmer if database fails
        return {
            'id': 1,
            'manager_name': 'Unknown',
            'farm_name': 'Unknown Farm',
            'city': 'Unknown'
        }


async def store_whatsapp_message(from_number: str, message_body: str, message_sid: str = None, farmer_id: int = None) -> Optional[int]:
    """Store incoming WhatsApp message in database"""
    try:
        # Use provided farmer_id or default
        if not farmer_id:
            farmer_id = 1  # Default for testing
        
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            # Store in incoming_messages table
            result = await conn.fetchval("""
                INSERT INTO incoming_messages 
                (farmer_id, phone_number, message_text, role, timestamp, message_sid)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """, farmer_id, from_number, message_body, 'user', datetime.utcnow(), message_sid)
            
            logger.info(f"Stored WhatsApp message {result} from {from_number}")
            return result
            
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"Error storing WhatsApp message: {str(e)}")
        return None


@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """
    Main webhook endpoint for incoming WhatsApp messages with comprehensive debugging
    """
    logger.info("=== WHATSAPP WEBHOOK START ===")
    resp = MessagingResponse()
    
    try:
        # Log raw request for debugging
        try:
            body_bytes = await request.body()
            logger.info(f"Raw request body: {body_bytes.decode('utf-8')}")
        except Exception as body_error:
            logger.error(f"Error reading body: {str(body_error)}")
        
        # Get form data from Twilio
        form_data = await request.form()
        logger.info(f"Parsed form data: {dict(form_data)}")
        
        # Extract message details
        from_number = form_data.get('From', '').replace('whatsapp:', '')
        to_number = form_data.get('To', '').replace('whatsapp:', '')
        message_body = form_data.get('Body', '')
        message_sid = form_data.get('MessageSid', '')
        
        logger.info(f"Extracted - From: {from_number}, To: {to_number}, Body: {message_body}, SID: {message_sid}")
        
        # Validate Twilio signature (security check)
        if TWILIO_AUTH_TOKEN:
            signature = request.headers.get('X-Twilio-Signature', '')
            url = f"{BASE_URL}/api/v1/whatsapp/webhook"
            
            validator = RequestValidator(TWILIO_AUTH_TOKEN)
            request_valid = validator.validate(
                url,
                dict(form_data),
                signature
            )
            
            if not request_valid:
                logger.warning(f"Invalid Twilio signature from {from_number}")
                # In production, uncomment to enforce security:
                # raise HTTPException(status_code=403, detail="Invalid signature")
        
        # Test database connection first
        logger.info("Testing database connection...")
        try:
            if DATABASE_URL:
                conn = await asyncpg.connect(DATABASE_URL)
                await conn.fetchval("SELECT 1")
                await conn.close()
                logger.info("Database connection: OK")
            else:
                logger.error("DATABASE_URL not set!")
                resp.message("Debug: DATABASE_URL not configured")
                return Response(content=str(resp), media_type="application/xml")
        except Exception as db_error:
            logger.error(f"Database connection error: {str(db_error)}")
            import traceback
            logger.error(f"DB traceback: {traceback.format_exc()}")
            resp.message(f"Debug: DB Error - {str(db_error)[:100]}")
            return Response(content=str(resp), media_type="application/xml")
        
        # Get or create farmer
        logger.info("Getting/creating farmer...")
        try:
            farmer = await get_or_create_farmer_by_phone(from_number)
            farmer_id = farmer['id']
            logger.info(f"Farmer retrieved/created: ID={farmer_id}, Name={farmer.get('manager_name')}")
        except Exception as farmer_error:
            logger.error(f"Farmer lookup error: {str(farmer_error)}")
            import traceback
            logger.error(f"Farmer traceback: {traceback.format_exc()}")
            resp.message(f"Debug: Farmer Error - {str(farmer_error)[:100]}")
            return Response(content=str(resp), media_type="application/xml")
        
        # Store message in database
        logger.info("Storing message in database...")
        try:
            message_id = await store_whatsapp_message(from_number, message_body, message_sid, farmer_id)
            logger.info(f"Message stored with ID: {message_id}")
        except Exception as store_error:
            logger.error(f"Message storage error: {str(store_error)}")
            # Continue anyway
        
        # Test CAVA import
        logger.info("Testing CAVA import...")
        try:
            from modules.cava.chat_engine import get_cava_engine
            logger.info("CAVA import successful")
        except Exception as import_error:
            logger.error(f"CAVA import error: {str(import_error)}")
            import traceback
            logger.error(f"Import traceback: {traceback.format_exc()}")
            
            # Try alternative imports
            logger.info("Trying alternative CAVA imports...")
            try:
                import sys
                logger.info(f"Python path: {sys.path}")
                logger.info(f"Current directory: {os.getcwd()}")
                
                # List what's in modules directory
                modules_path = os.path.join(os.getcwd(), 'modules')
                if os.path.exists(modules_path):
                    logger.info(f"Modules directory contents: {os.listdir(modules_path)}")
                    cava_path = os.path.join(modules_path, 'cava')
                    if os.path.exists(cava_path):
                        logger.info(f"CAVA directory contents: {os.listdir(cava_path)}")
            except Exception as e:
                logger.error(f"Directory listing error: {str(e)}")
            
            resp.message(f"Debug: CAVA Import Error - {str(import_error)[:100]}")
            return Response(content=str(resp), media_type="application/xml")
        
        # Process message through CAVA chat engine
        logger.info("Starting CAVA processing...")
        try:
            # Get CAVA engine instance
            logger.info("Getting CAVA engine instance...")
            cava_engine = get_cava_engine()
            logger.info(f"CAVA engine obtained: {type(cava_engine)}")
            
            # Check initialization
            logger.info(f"CAVA initialized: {getattr(cava_engine, 'initialized', 'No initialized attribute')}")
            
            # Try to initialize if needed
            if hasattr(cava_engine, 'initialized') and not cava_engine.initialized:
                logger.info("Initializing CAVA engine...")
                await cava_engine.initialize()
                logger.info("CAVA engine initialized")
            
            # Build farmer context
            farmer_context = {
                "farmer_id": farmer_id,
                "farmer_name": farmer.get('manager_name', 'Farmer'),
                "farm_name": farmer.get('farm_name', 'Farm'),
                "location": farmer.get('city', 'Unknown'),
                "phone": from_number,
                "weather": {},
                "fields": []
            }
            logger.info(f"Farmer context: {farmer_context}")
            
            # Get AI response from CAVA
            logger.info("Calling CAVA chat method...")
            result = await cava_engine.chat(
                session_id=f"whatsapp_{from_number}",
                message=message_body,
                farmer_context=farmer_context
            )
            logger.info(f"CAVA result: {result}")
            
            if result.get("success"):
                cava_response = result["response"]
                logger.info(f"CAVA response success: {cava_response[:100]}...")
            else:
                logger.error(f"CAVA returned error: {result.get('error')}")
                cava_response = f"Debug: CAVA returned error - {result.get('error', 'Unknown error')}"
                
        except Exception as cava_error:
            logger.error(f"CAVA processing error: {str(cava_error)}")
            logger.error(f"Error type: {type(cava_error)}")
            import traceback
            tb = traceback.format_exc()
            logger.error(f"Full traceback: {tb}")
            
            # Return detailed error for debugging
            cava_response = f"Debug: CAVA Error - {str(cava_error)[:200]}"
        
        # Create TwiML response with CAVA's intelligent response
        resp.message(cava_response)
        
        # Return TwiML response
        return Response(content=str(resp), media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {str(e)}")
        import traceback
        logger.error(f"Webhook error traceback: {traceback.format_exc()}")
        
        # Return error message instead of empty response
        resp.message(f"System error: {str(e)[:100]}...")
        return Response(content=str(resp), media_type="application/xml")


@router.post("/fallback")
async def whatsapp_fallback(request: Request):
    """
    Fallback webhook for handling failed message delivery
    Twilio calls this when primary webhook fails
    """
    try:
        form_data = await request.form()
        
        # Log fallback event
        from_number = form_data.get('From', '').replace('whatsapp:', '')
        error_code = form_data.get('ErrorCode', 'Unknown')
        
        logger.error(f"WhatsApp fallback triggered for {from_number}, error: {error_code}")
        
        # Return simple response
        resp = MessagingResponse()
        resp.message("Žao nam je, dogodila se greška. Molimo pokušajte ponovo.")
        
        return Response(content=str(resp), media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error in WhatsApp fallback: {str(e)}")
        return {"status": "fallback_error"}


@router.post("/status")
async def whatsapp_status(request: Request):
    """
    Status callback webhook for tracking message delivery
    Twilio sends updates here about message status
    """
    try:
        form_data = await request.form()
        
        # Extract status information
        message_sid = form_data.get('MessageSid', '')
        message_status = form_data.get('MessageStatus', '')
        to_number = form_data.get('To', '').replace('whatsapp:', '')
        
        logger.info(f"WhatsApp status update: {message_sid} is {message_status}")
        
        # Could store status updates in database for tracking
        # For now, just log them
        
        return {"status": "received", "message_status": message_status}
        
    except Exception as e:
        logger.error(f"Error processing status callback: {str(e)}")
        return {"status": "error"}


@router.get("/config")
async def get_whatsapp_config():
    """
    Returns all webhook URLs needed for Twilio configuration
    Visit this endpoint after deployment to get URLs for Twilio setup
    """
    return {
        "base_url": BASE_URL,
        "webhook_url": f"{BASE_URL}/api/v1/whatsapp/webhook",
        "fallback_url": f"{BASE_URL}/api/v1/whatsapp/fallback",
        "status_callback_url": f"{BASE_URL}/api/v1/whatsapp/status",
        "instructions": "Copy these URLs to Twilio WhatsApp Sender configuration",
        "twilio_console": "https://console.twilio.com/us1/develop/sms/senders/whatsapp-senders",
        "whatsapp_number": "+385919857451",
        "notes": {
            "webhook": "Main endpoint for incoming messages",
            "fallback": "Backup endpoint if main webhook fails",
            "status": "Receives delivery status updates"
        }
    }


@router.post("/test")
async def test_whatsapp():
    """
    Test endpoint to verify webhooks are working
    Can be called to check if the module is deployed correctly
    """
    return {
        "status": "working",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "webhook": "ready",
            "fallback": "ready",
            "status": "ready",
            "config": "ready"
        },
        "environment": {
            "auth_token_set": bool(TWILIO_AUTH_TOKEN),
            "database_url_set": bool(DATABASE_URL),
            "base_url": BASE_URL
        }
    }


@router.get("/health")
async def whatsapp_health():
    """Health check endpoint for WhatsApp integration"""
    health_status = {
        "service": "whatsapp_webhook",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "twilio_auth": "configured" if TWILIO_AUTH_TOKEN else "missing",
            "database": "configured" if DATABASE_URL else "missing",
            "base_url": BASE_URL
        }
    }
    
    # Check database connectivity
    if DATABASE_URL:
        try:
            conn = await asyncpg.connect(DATABASE_URL)
            await conn.fetchval("SELECT 1")
            await conn.close()
            health_status["checks"]["database_connection"] = "connected"
        except Exception as e:
            health_status["checks"]["database_connection"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
    
    return health_status


@router.post("/test-simple")
async def test_simple_response():
    """Simple test endpoint that doesn't use CAVA"""
    try:
        # Test basic functionality
        resp = MessagingResponse()
        resp.message("Hello! This is a simple test response from AVA OLO. The webhook is working!")
        return Response(content=str(resp), media_type="application/xml")
    except Exception as e:
        return {"error": str(e)}


@router.post("/webhook-debug")
async def whatsapp_webhook_debug(request: Request):
    """Debug version of webhook - returns simple response to test basic functionality"""
    try:
        # Get form data
        form_data = await request.form()
        message_body = form_data.get('Body', 'No message')
        from_number = form_data.get('From', 'Unknown')
        
        # Create simple response
        resp = MessagingResponse()
        resp.message(f"DEBUG: I received your message '{message_body}' from {from_number}. Basic webhook is working!")
        
        return Response(content=str(resp), media_type="application/xml")
        
    except Exception as e:
        # Even simpler fallback
        resp = MessagingResponse()
        resp.message(f"DEBUG ERROR: {str(e)}")
        return Response(content=str(resp), media_type="application/xml")


@router.get("/test-cava")
async def test_cava_engine():
    """Test if CAVA engine can be imported and initialized"""
    debug_info = {
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Test 1: Can we import CAVA?
    try:
        from modules.cava.chat_engine import get_cava_engine
        debug_info["checks"]["import_cava"] = "success"
    except Exception as e:
        debug_info["checks"]["import_cava"] = f"failed: {str(e)}"
        import traceback
        debug_info["import_traceback"] = traceback.format_exc()
        return debug_info
    
    # Test 2: Can we get CAVA instance?
    try:
        cava = get_cava_engine()
        debug_info["checks"]["get_cava_instance"] = "success"
        debug_info["checks"]["cava_type"] = str(type(cava))
        debug_info["checks"]["cava_initialized"] = getattr(cava, 'initialized', 'No initialized attribute')
    except Exception as e:
        debug_info["checks"]["get_cava_instance"] = f"failed: {str(e)}"
        return debug_info
    
    # Test 3: Can we initialize CAVA?
    try:
        if hasattr(cava, 'initialized') and not cava.initialized:
            await cava.initialize()
        debug_info["checks"]["initialize_cava"] = "success"
    except Exception as e:
        debug_info["checks"]["initialize_cava"] = f"failed: {str(e)}"
    
    # Test 4: Can we call chat?
    try:
        result = await cava.chat(
            session_id="test_session",
            message="Hello, this is a test",
            farmer_context={"farmer_name": "Test User"}
        )
        debug_info["checks"]["cava_chat_call"] = "success"
        debug_info["cava_response"] = result
    except Exception as e:
        debug_info["checks"]["cava_chat_call"] = f"failed: {str(e)}"
        import traceback
        debug_info["chat_traceback"] = traceback.format_exc()
    
    return debug_info


@router.post("/webhook-minimal")
async def whatsapp_webhook_minimal(request: Request):
    """Minimal webhook that mimics the test-cava endpoint success"""
    resp = MessagingResponse()
    
    try:
        # Get message from form data
        form_data = await request.form()
        message_body = form_data.get('Body', 'Hello')
        
        # Import and use CAVA exactly like test-cava does
        from modules.cava.chat_engine import get_cava_engine
        cava = get_cava_engine()
        
        # Initialize if needed (same as test)
        if hasattr(cava, 'initialized') and not cava.initialized:
            await cava.initialize()
        
        # Call chat with minimal context (same as test)
        result = await cava.chat(
            session_id="whatsapp_test",
            message=message_body,
            farmer_context={"farmer_name": "WhatsApp User"}
        )
        
        if result.get("success"):
            resp.message(result["response"])
        else:
            resp.message(f"CAVA error: {result.get('error', 'Unknown')}")
            
    except Exception as e:
        resp.message(f"Minimal webhook error: {str(e)}")
    
    return Response(content=str(resp), media_type="application/xml")


@router.get("/debug-imports")
async def debug_imports():
    """Debug import paths and module structure"""
    import sys
    import os
    
    debug_info = {
        "current_dir": os.getcwd(),
        "python_path": sys.path[:5],  # First 5 paths
        "modules_in_cwd": [],
        "cava_search": []
    }
    
    # List current directory
    try:
        debug_info["cwd_contents"] = os.listdir(os.getcwd())
    except:
        debug_info["cwd_contents"] = "Error listing cwd"
    
    # Check modules directory
    modules_path = os.path.join(os.getcwd(), 'modules')
    if os.path.exists(modules_path):
        try:
            debug_info["modules_contents"] = os.listdir(modules_path)
            
            # Check CAVA directory
            cava_path = os.path.join(modules_path, 'cava')
            if os.path.exists(cava_path):
                debug_info["cava_contents"] = os.listdir(cava_path)
        except Exception as e:
            debug_info["modules_error"] = str(e)
    
    # Try different import methods
    import_results = {}
    
    # Method 1: Direct import
    try:
        from modules.cava.chat_engine import get_cava_engine
        import_results["direct_import"] = "Success"
    except Exception as e:
        import_results["direct_import"] = str(e)
    
    # Method 2: Module import
    try:
        import modules.cava.chat_engine
        import_results["module_import"] = "Success"
    except Exception as e:
        import_results["module_import"] = str(e)
    
    # Method 3: Check if chat_engine exists
    try:
        chat_engine_path = os.path.join(os.getcwd(), 'modules', 'cava', 'chat_engine.py')
        import_results["chat_engine_exists"] = os.path.exists(chat_engine_path)
    except:
        import_results["chat_engine_exists"] = "Error checking"
    
    debug_info["import_results"] = import_results
    
    return debug_info