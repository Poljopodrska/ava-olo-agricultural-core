from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
import hashlib

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    phone: str
    role: str = "farmer"

# In-memory storage for demo
users = {}

@router.post("/login")
async def login(request: LoginRequest):
    """Simple login endpoint"""
    # For demo, accept any password
    token = hashlib.md5(f"{request.username}-{datetime.now()}".encode()).hexdigest()
    
    return JSONResponse(content={
        "success": True,
        "token": token,
        "user": {
            "id": 1,
            "username": request.username,
            "role": "farmer"
        }
    })

@router.post("/register")
async def register(request: RegisterRequest):
    """Simple registration endpoint"""
    # For demo, always succeed
    users[request.username] = {
        "phone": request.phone,
        "role": request.role
    }
    
    return JSONResponse(content={
        "success": True,
        "message": "Registration successful",
        "user": {
            "username": request.username,
            "role": request.role
        }
    })

@router.post("/logout")
async def logout():
    """Logout endpoint"""
    return JSONResponse(content={
        "success": True,
        "message": "Logged out successfully"
    })