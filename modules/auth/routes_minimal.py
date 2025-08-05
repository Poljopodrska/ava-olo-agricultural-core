#!/usr/bin/env python3
"""
Minimal authentication routes for Phase 3
No complex dependencies, just basic auth endpoints
"""
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# Templates
template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates")
templates = Jinja2Templates(directory=template_dir)

@router.get("/signin", response_class=HTMLResponse)
async def signin_page(request: Request):
    """Display sign-in page"""
    try:
        return templates.TemplateResponse("auth/signin.html", {
            "request": request,
            "version": "v4.8.8",
            "language": "en",
            "t": {
                "sign_in_title": "Sign In",
                "sign_in_subtitle": "Agricultural Virtual Assistant Optimizing Land Operations",
                "whatsapp_label": "WhatsApp Number",
                "whatsapp_placeholder": "e.g., +359888123456",
                "password_label": "Password",
                "password_placeholder": "Enter your password",
                "sign_in_button": "Sign In",
                "no_account": "Don't have an account?",
                "register_link": "Register here"
            }
        })
    except Exception as e:
        logger.error(f"Error in signin_page: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Display registration page"""
    try:
        return templates.TemplateResponse("auth/register_split.html", {
            "request": request,
            "version": "v4.8.8",
            "language": "en",
            "t": {
                "register_title": "Create Account",
                "register_subtitle": "Agricultural Virtual Assistant Optimizing Land Operations",
                "first_name_label": "First Name",
                "first_name_placeholder": "Enter your first name",
                "last_name_label": "Last Name",
                "last_name_placeholder": "Enter your last name",
                "whatsapp_label": "WhatsApp Number",
                "whatsapp_placeholder": "e.g., +359888123456",
                "email_label": "Email",
                "email_placeholder": "your@email.com",
                "password_label": "Password",
                "password_placeholder": "Enter your password",
                "confirm_password_label": "Confirm Password",
                "confirm_password_placeholder": "Re-enter your password",
                "register_button": "Create Account",
                "have_account": "Already have an account?",
                "signin_link": "Sign in here"
            }
        })
    except Exception as e:
        logger.error(f"Error in register_page: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.post("/signin")
async def signin_submit(request: Request):
    """Process sign-in - minimal version"""
    # For now, just redirect to dashboard
    return RedirectResponse(url="/farmer/dashboard", status_code=303)

@router.post("/register")
async def register_submit(request: Request):
    """Process registration - minimal version"""
    # For now, just redirect to dashboard
    return RedirectResponse(url="/farmer/dashboard", status_code=303)

@router.get("/logout")
async def logout():
    """Log out user"""
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="farmer_id")
    response.delete_cookie(key="farmer_name")
    return response