#!/usr/bin/env python3
"""
Authentication routes for AVA OLO Farmer Portal
WhatsApp number + password authentication system
"""
from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from passlib.context import CryptContext
import re
from typing import Optional
import secrets
import logging

from modules.core.database_manager import get_db_manager
from modules.core.config import VERSION

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])
templates = Jinja2Templates(directory="templates")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Basic security
security = HTTPBasic()

def validate_whatsapp_number(phone: str) -> bool:
    """Validate WhatsApp phone number format"""
    # Remove all non-digits
    digits_only = re.sub(r'\D', '', phone)
    
    # Should be 10-15 digits (international format)
    if len(digits_only) < 10 or len(digits_only) > 15:
        return False
    
    # Should start with country code (not starting with 0)
    if digits_only.startswith('0'):
        return False
        
    return True

def format_whatsapp_number(phone: str) -> str:
    """Format WhatsApp number to standard format"""
    digits_only = re.sub(r'\D', '', phone)
    
    # Add + prefix for international format
    if not digits_only.startswith('+'):
        return '+' + digits_only
    return digits_only

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)

async def get_farmer_by_whatsapp(whatsapp_number: str):
    """Get farmer by WhatsApp number from database"""
    db_manager = get_db_manager()
    
    try:
        # Fixed query without 'name' column
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
        WHERE (whatsapp_number = %s OR wa_phone_number = %s) 
        AND COALESCE(is_active, true) = true
        """
        result = db_manager.execute_query(query, (whatsapp_number, whatsapp_number))
        
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
    except Exception as e:
        logger.error(f"Database error in get_farmer_by_whatsapp: {e}")
        logger.error(f"Query was: {query}")
        logger.error(f"Parameters: {(whatsapp_number, whatsapp_number)}")
        import traceback
        traceback.print_exc()
        return None
    
    return None

async def create_farmer_account(first_name: str, last_name: str, whatsapp_number: str, email: str, password: str):
    """Create new farmer account"""
    db_manager = get_db_manager()
    
    try:
        # Check if farmer already exists
        existing_farmer = await get_farmer_by_whatsapp(whatsapp_number)
        if existing_farmer:
            raise HTTPException(
                status_code=400, 
                detail="Farmer with this WhatsApp number already exists"
            )
        
        # Hash password
        password_hash = get_password_hash(password)
        
        # Insert new farmer
        query = """
        INSERT INTO farmers (
            manager_name, 
            manager_last_name, 
            email, 
            wa_phone_number, 
            phone,
            password_hash, 
            is_active, 
            created_at,
            whatsapp_number,
            farm_name,
            country
        )
        VALUES (%s, %s, %s, %s, %s, %s, true, NOW(), %s, %s, %s)
        RETURNING id
        """
        
        # Default farm name from farmer name
        default_farm_name = f"{first_name} {last_name}'s Farm".strip()
        
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
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to create farmer account")

@router.get("/signin", response_class=HTMLResponse)
async def signin_page(request: Request):
    """Display sign-in page"""
    return templates.TemplateResponse("auth/signin.html", {
        "request": request,
        "version": VERSION
    })

@router.post("/signin")
async def signin_submit(
    request: Request,
    whatsapp_number: str = Form(...),
    password: str = Form(...)
):
    """Process sign-in form submission"""
    
    # Validate WhatsApp number
    if not validate_whatsapp_number(whatsapp_number):
        return templates.TemplateResponse("auth/signin.html", {
            "request": request,
            "version": VERSION,
            "error": "Please enter a valid WhatsApp number (e.g., +359123456789)"
        })
    
    # Format WhatsApp number
    formatted_number = format_whatsapp_number(whatsapp_number)
    
    # Get farmer from database
    farmer = await get_farmer_by_whatsapp(formatted_number)
    
    if not farmer:
        return templates.TemplateResponse("auth/signin.html", {
            "request": request,
            "version": VERSION,
            "error": "No account found with this WhatsApp number"
        })
    
    # Check if password_hash exists
    if not farmer.get('password_hash'):
        return templates.TemplateResponse("auth/signin.html", {
            "request": request,
            "version": VERSION,
            "error": "Account not set up for password login. Please register again."
        })
    
    # Verify password
    if not verify_password(password, farmer['password_hash']):
        return templates.TemplateResponse("auth/signin.html", {
            "request": request,
            "version": VERSION,
            "error": "Incorrect password"
        })
    
    # Successful login - redirect to farmer dashboard
    response = RedirectResponse(url="/farmer/dashboard", status_code=303)
    response.set_cookie(key="farmer_id", value=str(farmer['farmer_id']), httponly=True)
    response.set_cookie(key="farmer_name", value=farmer['name'], httponly=True)
    
    return response

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Display traditional form registration"""
    return templates.TemplateResponse("auth/register_split.html", {
        "request": request,
        "version": VERSION
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
    
    # Validate required fields
    if not first_name.strip():
        return templates.TemplateResponse("auth/register_split.html", {
            "request": request,
            "version": VERSION,
            "error": "First name is required"
        })
    
    if not last_name.strip():
        return templates.TemplateResponse("auth/register_split.html", {
            "request": request,
            "version": VERSION,
            "error": "Last name is required"
        })
    
    # Validate WhatsApp number
    if not validate_whatsapp_number(whatsapp_number):
        return templates.TemplateResponse("auth/register_split.html", {
            "request": request,
            "version": VERSION,
            "error": "Please enter a valid WhatsApp number (e.g., +359123456789)"
        })
    
    # Validate email format
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    if not email_pattern.match(email):
        return templates.TemplateResponse("auth/register_split.html", {
            "request": request,
            "version": VERSION,
            "error": "Please enter a valid email address"
        })
    
    # Validate password
    if len(password) < 8:
        return templates.TemplateResponse("auth/register_split.html", {
            "request": request,
            "version": VERSION,
            "error": "Password must be at least 8 characters long"
        })
    
    # Validate password confirmation
    if password != confirm_password:
        return templates.TemplateResponse("auth/register_split.html", {
            "request": request,
            "version": VERSION,
            "error": "Passwords do not match"
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
            "error": e.detail
        })
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return templates.TemplateResponse("auth/register_split.html", {
            "request": request,
            "version": VERSION,
            "error": "An error occurred while creating your account. Please try again."
        })

@router.get("/logout")
async def logout():
    """Log out user"""
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="farmer_id")
    response.delete_cookie(key="farmer_name")
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

# Keep other endpoints for backward compatibility
@router.post("/admin-login")
async def admin_login(request: Request):
    """Admin login bypass for testing"""
    response = JSONResponse(content={"success": True})
    response.set_cookie(key="farmer_id", value="1", httponly=True)
    response.set_cookie(key="farmer_name", value="Admin User", httponly=True)
    response.set_cookie(key="is_admin", value="true", httponly=True)
    return response

# Other registration variants
@router.get("/register/cava", response_class=HTMLResponse)
async def cava_register_page(request: Request):
    """Display CAVA-powered intelligent registration"""
    return templates.TemplateResponse("auth/register_cava.html", {
        "request": request,
        "version": VERSION
    })

@router.get("/register/true", response_class=HTMLResponse)
async def true_register_page(request: Request):
    """Display TRUE CAVA registration - pure conversation"""
    return templates.TemplateResponse("true_cava_registration.html", {
        "request": request,
        "version": VERSION
    })

@router.get("/register/chat", response_class=HTMLResponse)
async def chat_register_page(request: Request):
    """Display simple chat registration - Step 1"""
    return templates.TemplateResponse("register_chat.html", {
        "request": request,
        "version": VERSION
    })

@router.get("/register/pure", response_class=HTMLResponse)
async def pure_chat_page(request: Request):
    """Display PURE chat - NO validation or hardcoding"""
    return templates.TemplateResponse("pure_chat.html", {
        "request": request,
        "version": VERSION
    })

@router.get("/register/llm", response_class=HTMLResponse)
async def llm_register_page(request: Request):
    """Display LLM registration - EXACT same as dashboard chat"""
    return templates.TemplateResponse("register_llm.html", {
        "request": request,
        "version": VERSION
    })

@router.get("/register/enhanced", response_class=HTMLResponse)
async def enhanced_register_page(request: Request):
    """Display enhanced CAVA registration with full validation"""
    return templates.TemplateResponse("register_enhanced.html", {
        "request": request,
        "version": VERSION
    })