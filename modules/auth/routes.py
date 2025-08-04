#!/usr/bin/env python3
"""
Authentication routes - v2 with proper validation
Only checks active farmers in the farmers table
"""
from fastapi import APIRouter, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
# Removed passlib - using standard library only
import re
import logging
from modules.core.config import VERSION
from modules.core.database_manager import get_db_manager
from modules.core.translations import get_translations
from modules.core.language_service import get_language_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="templates")

# Password hashing using standard library
import hashlib
import secrets

def validate_whatsapp_number(number: str) -> bool:
    """Validate WhatsApp number format"""
    # Remove all spaces and special characters except +
    cleaned = re.sub(r'[^\d+]', '', number)
    
    # Must have only digits and optionally start with +
    if not re.match(r'^\+?\d+$', cleaned):
        return False
    
    # Must have at least 10 digits (minimum for most countries)
    digits_only = cleaned.replace('+', '')
    if len(digits_only) < 10 or len(digits_only) > 15:
        return False
    
    return True

def format_whatsapp_number(number: str) -> str:
    """Format WhatsApp number to standard format"""
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', number)
    
    # Remove + to get digits only
    digits_only = cleaned.replace('+', '')
    
    # Add + prefix for international format
    if not digits_only.startswith('+'):
        return '+' + digits_only
    return digits_only

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        if not hashed_password or '$' not in hashed_password:
            return False
        parts = hashed_password.split('$')
        if len(parts) != 3 or parts[0] != 'pbkdf2_sha256':
            return False
        salt = parts[1]
        key = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return key.hex() == parts[2]
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Generate password hash"""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"pbkdf2_sha256${salt}${key.hex()}"

async def get_active_farmer_by_whatsapp(whatsapp_number: str):
    """Get ONLY active farmer from farmers table (not archived/deleted farmers)"""
    db_manager = get_db_manager()
    
    try:
        # Only search ACTIVE farmers in farmers table
        query = """
        SELECT id, 
               manager_name,
               manager_last_name,
               email, 
               COALESCE(whatsapp_number, wa_phone_number) as whatsapp_number, 
               password_hash, 
               created_at, 
               COALESCE(is_active, true) as is_active
        FROM farmers 
        WHERE (whatsapp_number = %s OR wa_phone_number = %s OR phone = %s)
              AND (is_active = true OR is_active IS NULL)
        """
        result = db_manager.execute_query(query, (whatsapp_number, whatsapp_number, whatsapp_number))
        
        if result and 'rows' in result and len(result['rows']) > 0:
            row = result['rows'][0]
            # Combine first and last name
            full_name = f"{row[1] or ''} {row[2] or ''}".strip()
            return {
                'farmer_id': row[0],
                'name': full_name,
                'first_name': row[1],
                'last_name': row[2],
                'email': row[3],
                'whatsapp_number': row[4],
                'password_hash': row[5],
                'created_at': row[6],
                'is_active': row[7]
            }
        return None
    except Exception as e:
        logger.error(f"Error getting farmer by WhatsApp: {e}")
        return None

async def create_farmer_account(first_name: str, last_name: str, whatsapp_number: str, email: str, password: str):
    """Create new farmer account"""
    db_manager = get_db_manager()
    
    try:
        # Check if farmer already exists IN THE ACTIVE FARMERS TABLE ONLY
        existing_farmer = await get_active_farmer_by_whatsapp(whatsapp_number)
        if existing_farmer:
            # Provide helpful message with existing farmer info
            existing_name = existing_farmer.get('name', 'Unknown')
            raise HTTPException(
                status_code=400, 
                detail=f"This WhatsApp number is already registered to {existing_name}. Please use Sign In instead, or contact support if you need help accessing your account."
            )
        
        # Hash password
        password_hash = get_password_hash(password)
        
        # Create default farm name
        default_farm_name = f"{first_name} {last_name}'s Farm"
        
        # Insert into farmers table
        query = """
        INSERT INTO farmers (
            manager_name, manager_last_name, email, phone, 
            wa_phone_number, password_hash, whatsapp_number, 
            farm_name, country
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        
        result = db_manager.execute_query(
            query, 
            (first_name, last_name, email, whatsapp_number, 
             whatsapp_number, password_hash, whatsapp_number, 
             default_farm_name, 'Bulgaria')
        )
        
        if result and 'rows' in result and len(result['rows']) > 0:
            return result['rows'][0][0]  # Return farmer_id
        else:
            logger.error("No rows returned from INSERT query")
            raise HTTPException(status_code=500, detail="Failed to create farmer account")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error creating farmer: {e}")
        raise HTTPException(status_code=500, detail="Failed to create farmer account")

@router.get("/chat", response_class=HTMLResponse)
async def pure_chat_page(request: Request):
    """Pure chat interface with CAVA"""
    return templates.TemplateResponse("pure_chat.html", {
        "request": request,
        "version": VERSION
    })

@router.get("/signin", response_class=HTMLResponse)
async def signin_page(request: Request):
    """Display sign-in page with language detection"""
    # Detect language from IP address
    language_service = get_language_service()
    
    # Get client IP - check for forwarded headers first (for deployment behind proxy)
    client_ip = request.headers.get("X-Forwarded-For")
    if client_ip:
        client_ip = client_ip.split(",")[0].strip()
    elif request.client:
        client_ip = request.client.host
    else:
        client_ip = "127.0.0.1"
    
    logger.info(f"Auth page accessed from IP: {client_ip}")
    detected_language = await language_service.detect_language_from_ip(client_ip)
    
    # Get translations for the detected language
    translations = get_translations(detected_language)
    
    return templates.TemplateResponse("auth/signin.html", {
        "request": request,
        "version": VERSION,
        "language": detected_language,
        "t": translations
    })

@router.post("/signin")
async def signin_submit(
    request: Request,
    whatsapp_number: str = Form(...),
    password: str = Form(...)
):
    """Process sign-in form submission"""
    
    # Get language detection for error pages
    language_service = get_language_service()
    client_ip = request.headers.get("X-Forwarded-For")
    if client_ip:
        client_ip = client_ip.split(",")[0].strip()
    elif request.client:
        client_ip = request.client.host
    else:
        client_ip = "127.0.0.1"
    detected_language = await language_service.detect_language_from_ip(client_ip)
    translations = get_translations(detected_language)
    
    # Validate WhatsApp number
    if not validate_whatsapp_number(whatsapp_number):
        return templates.TemplateResponse("auth/signin.html", {
            "request": request,
            "version": VERSION,
            "error": "Please enter a valid WhatsApp number (e.g., +359123456789)",
            "language": detected_language,
            "t": translations
        })
    
    # Format WhatsApp number
    formatted_number = format_whatsapp_number(whatsapp_number)
    
    # Get farmer from database (ACTIVE FARMERS ONLY)
    farmer = await get_active_farmer_by_whatsapp(formatted_number)
    
    if not farmer:
        return templates.TemplateResponse("auth/signin.html", {
            "request": request,
            "version": VERSION,
            "error": "No account found with this WhatsApp number",
            "language": detected_language,
            "t": translations
        })
    
    # Check if password_hash exists
    if not farmer.get('password_hash'):
        return templates.TemplateResponse("auth/signin.html", {
            "request": request,
            "version": VERSION,
            "error": "Account not set up for password login. Please register again.",
            "language": detected_language,
            "t": translations
        })
    
    # Verify password
    if not verify_password(password, farmer['password_hash']):
        return templates.TemplateResponse("auth/signin.html", {
            "request": request,
            "version": VERSION,
            "error": "Incorrect password",
            "language": detected_language,
            "t": translations
        })
    
    # Successful login - redirect to farmer dashboard
    response = RedirectResponse(url="/farmer/dashboard", status_code=303)
    response.set_cookie(key="farmer_id", value=str(farmer['farmer_id']), httponly=True)
    response.set_cookie(key="farmer_name", value=farmer['name'], httponly=True)
    
    return response

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Display traditional form registration with language detection"""
    # Detect language from IP address
    language_service = get_language_service()
    
    # Get client IP - check for forwarded headers first (for deployment behind proxy)
    client_ip = request.headers.get("X-Forwarded-For")
    if client_ip:
        client_ip = client_ip.split(",")[0].strip()
    elif request.client:
        client_ip = request.client.host
    else:
        client_ip = "127.0.0.1"
    
    logger.info(f"Auth page accessed from IP: {client_ip}")
    detected_language = await language_service.detect_language_from_ip(client_ip)
    
    # Get translations for the detected language
    translations = get_translations(detected_language)
    
    return templates.TemplateResponse("auth/register_split.html", {
        "request": request,
        "version": VERSION,
        "language": detected_language,
        "t": translations
    })

@router.post("/register")
async def register_submit(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    whatsapp_number: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    """Process registration form submission"""
    
    # Get language detection for error pages
    language_service = get_language_service()
    client_ip = request.headers.get("X-Forwarded-For")
    if client_ip:
        client_ip = client_ip.split(",")[0].strip()
    elif request.client:
        client_ip = request.client.host
    else:
        client_ip = "127.0.0.1"
    detected_language = await language_service.detect_language_from_ip(client_ip)
    translations = get_translations(detected_language)
    
    # Validate required fields
    if not first_name.strip():
        return templates.TemplateResponse("auth/register_split.html", {
            "request": request,
            "version": VERSION,
            "error": "First name is required",
            "language": detected_language,
            "t": translations
        })
    
    if not last_name.strip():
        return templates.TemplateResponse("auth/register_split.html", {
            "request": request,
            "version": VERSION,
            "error": "Last name is required",
            "language": detected_language,
            "t": translations
        })
    
    # Validate WhatsApp number
    if not validate_whatsapp_number(whatsapp_number):
        return templates.TemplateResponse("auth/register_split.html", {
            "request": request,
            "version": VERSION,
            "error": "Please enter a valid WhatsApp number (e.g., +359123456789)",
            "language": detected_language,
            "t": translations
        })
    
    # Validate email format
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    if not email_pattern.match(email):
        return templates.TemplateResponse("auth/register_split.html", {
            "request": request,
            "version": VERSION,
            "error": "Please enter a valid email address",
            "language": detected_language,
            "t": translations
        })
    
    # Validate password
    if len(password) < 8:
        return templates.TemplateResponse("auth/register_split.html", {
            "request": request,
            "version": VERSION,
            "error": "Password must be at least 8 characters long",
            "language": detected_language,
            "t": translations
        })
    
    # Validate password confirmation
    if password != confirm_password:
        return templates.TemplateResponse("auth/register_split.html", {
            "request": request,
            "version": VERSION,
            "error": "Passwords do not match",
            "language": detected_language,
            "t": translations
        })
    
    # Format WhatsApp number
    formatted_number = format_whatsapp_number(whatsapp_number)
    
    try:
        # Create farmer account
        farmer_id = await create_farmer_account(
            first_name.strip(), 
            last_name.strip(), 
            formatted_number, 
            email, 
            password
        )
        
        if farmer_id:
            # Successful registration - redirect to farmer dashboard
            response = RedirectResponse(url="/farmer/dashboard", status_code=303)
            response.set_cookie(key="farmer_id", value=str(farmer_id), httponly=True)
            response.set_cookie(key="farmer_name", value=f"{first_name} {last_name}".strip(), httponly=True)
            
            return response
        else:
            raise HTTPException(status_code=500, detail="Failed to create account")
            
    except HTTPException as e:
        return templates.TemplateResponse("auth/register_split.html", {
            "request": request,
            "version": VERSION,
            "error": e.detail,
            "language": detected_language,
            "t": translations
        })
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return templates.TemplateResponse("auth/register_split.html", {
            "request": request,
            "version": VERSION,
            "error": "An error occurred while creating your account. Please try again.",
            "language": detected_language,
            "t": translations
        })

@router.get("/logout")
async def logout():
    """Log out user"""
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="farmer_id")
    response.delete_cookie(key="farmer_name")
    response.delete_cookie(key="is_admin")
    return response

async def get_current_farmer(request: Request) -> Optional[dict]:
    """Get current logged-in farmer from cookies"""
    farmer_id = request.cookies.get("farmer_id")
    farmer_name = request.cookies.get("farmer_name")
    
    if farmer_id and farmer_name:
        return {
            "farmer_id": int(farmer_id),
            "name": farmer_name
        }
    
    return None

async def require_auth(request: Request):
    """Dependency to require authentication"""
    farmer = await get_current_farmer(request)
    if not farmer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )
    return farmer