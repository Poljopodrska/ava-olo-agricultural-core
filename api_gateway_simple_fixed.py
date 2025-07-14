"""
Production-ready API Gateway with fixed authentication
Resolves event loop issues for AWS App Runner deployment
"""

# Import the existing API gateway
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api_gateway_simple import *
import logging

logger = logging.getLogger(__name__)

# Override the problematic authentication initialization
# with a lazy-loading production-ready approach

# Remove the existing authentication endpoints if they were registered
routes_to_remove = [
    "/api/v1/auth/login",
    "/api/v1/auth/register", 
    "/api/v1/auth/me",
    "/api/v1/auth/family",
    "/api/v1/auth/activity",
    "/api/v1/farmers/me",
    "/api/v1/conversations/me",
    "/api/v1/auth/status"
]

for route in routes_to_remove:
    for r in app.routes[:]:
        if hasattr(r, 'path') and r.path == route:
            app.routes.remove(r)

# Lazy authentication manager initialization
_auth_manager = None
_auth_middleware = None
_auth_deps = None

def get_auth_manager():
    """Lazy initialization of authentication manager"""
    global _auth_manager
    if _auth_manager is None:
        try:
            from implementation.farm_auth import FarmAuthManager
            _auth_manager = FarmAuthManager()
            logger.info("✅ Authentication manager initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize auth manager: {e}")
            raise
    return _auth_manager

def get_auth_middleware():
    """Lazy initialization of authentication middleware"""
    global _auth_middleware
    if _auth_middleware is None:
        try:
            from implementation.auth_middleware import AuthMiddleware
            _auth_middleware = AuthMiddleware(get_auth_manager())
            logger.info("✅ Authentication middleware initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize auth middleware: {e}")
            raise
    return _auth_middleware

def get_auth_deps():
    """Lazy initialization of authentication dependencies"""
    global _auth_deps
    if _auth_deps is None:
        try:
            from implementation.auth_middleware import AuthDependencies
            _auth_deps = AuthDependencies(get_auth_middleware())
            logger.info("✅ Authentication dependencies initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize auth deps: {e}")
            raise
    return _auth_deps

# Re-add authentication endpoints with lazy loading
try:
    from implementation.auth_middleware import AuthMiddleware, AuthDependencies
    from pydantic import BaseModel, Field
    from fastapi import Depends, HTTPException
    
    # Authentication request/response models
    class LoginRequest(BaseModel):
        wa_phone_number: str = Field(..., description="WhatsApp phone number")
        password: str = Field(..., description="User password")

    class RegisterUserRequest(BaseModel):
        wa_phone_number: str = Field(..., description="WhatsApp phone number")
        password: str = Field(..., description="User password")
        user_name: str = Field(..., description="User display name")
        role: str = Field(default="member", description="User role: owner, member, worker")

    class LoginResponse(BaseModel):
        success: bool
        token: Optional[str] = None
        user: Optional[Dict[str, Any]] = None
        message: Optional[str] = None

    # Authentication endpoints with lazy loading
    @app.post("/api/v1/auth/login", response_model=LoginResponse)
    async def login(request: LoginRequest):
        """Constitutional farmer login endpoint"""
        try:
            auth_manager = get_auth_manager()
            result = auth_manager.authenticate_user(
                request.wa_phone_number,
                request.password
            )
            
            if result['success']:
                return LoginResponse(
                    success=True,
                    token=result['token'],
                    user=result['user']
                )
            else:
                return LoginResponse(
                    success=False,
                    message=result.get('message', 'Authentication failed')
                )
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/v1/auth/register")
    async def register_user(
        request: RegisterUserRequest,
        current_user: Dict = Depends(lambda: get_auth_deps().require_role("owner"))
    ):
        """Register new family member (owner only)"""
        try:
            auth_manager = get_auth_manager()
            # Extract farmer_id from current user
            farmer_id = current_user.get('farmer_id')
            
            result = auth_manager.register_farm_user(
                farmer_id=farmer_id,
                wa_phone_number=request.wa_phone_number,
                password=request.password,
                user_name=request.user_name,
                role=request.role,
                created_by_user_id=current_user.get('id')
            )
            
            return result
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/v1/auth/me")
    async def get_current_user(current_user: Dict = Depends(lambda: get_auth_deps().get_current_user)):
        """Get current authenticated user info"""
        return {"success": True, "user": current_user}

    @app.get("/api/v1/auth/family")
    async def get_family_members(current_user: Dict = Depends(lambda: get_auth_deps().get_current_user)):
        """Get all family members for the farm"""
        try:
            auth_manager = get_auth_manager()
            farmer_id = current_user.get('farmer_id')
            members = auth_manager.get_farm_users(farmer_id)
            return {"success": True, "family_members": members}
        except Exception as e:
            logger.error(f"Error getting family members: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/v1/auth/activity")
    async def get_farm_activity(
        current_user: Dict = Depends(lambda: get_auth_deps().get_current_user),
        limit: int = 100
    ):
        """Get farm activity log"""
        try:
            auth_manager = get_auth_manager()
            farmer_id = current_user.get('farmer_id')
            activity = auth_manager.get_farm_activity_log(farmer_id, limit)
            return {"success": True, "activity": activity}
        except Exception as e:
            logger.error(f"Error getting activity log: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    # Enhanced endpoints with authentication
    @app.get("/api/v1/farmers/me")
    async def get_my_farmer_info(current_user: Dict = Depends(lambda: get_auth_deps().get_current_user)):
        """Get authenticated farmer's information"""
        try:
            farmer_id = current_user.get('farmer_id')
            farmer = await db_ops.get_farmer_by_id(farmer_id)
            return {"success": True, "farmer": farmer}
        except Exception as e:
            logger.error(f"Error getting farmer info: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/v1/conversations/me")
    async def get_my_conversations(
        current_user: Dict = Depends(lambda: get_auth_deps().get_current_user),
        limit: int = 50
    ):
        """Get authenticated user's conversations with audit trail"""
        try:
            farmer_id = current_user.get('farmer_id')
            user_id = current_user.get('id')
            
            # Get conversations
            conversations = await db_ops.get_farmer_conversations(farmer_id, limit)
            
            # Log activity
            auth_manager = get_auth_manager()
            auth_manager.log_activity(
                farmer_id=farmer_id,
                user_id=user_id,
                action="view_conversations",
                details={"count": len(conversations)}
            )
            
            return {
                "success": True, 
                "conversations": conversations,
                "accessed_by": current_user.get('user_name')
            }
        except Exception as e:
            logger.error(f"Error getting conversations: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    # Fallback status endpoint
    @app.get("/api/v1/auth/status")
    async def auth_status():
        """Check authentication system status"""
        try:
            # Try to initialize auth manager
            auth_manager = get_auth_manager()
            return {
                "authentication_enabled": True,
                "status": "operational",
                "features": [
                    "multi-user authentication",
                    "family member management",
                    "audit trail logging",
                    "role-based access control"
                ]
            }
        except Exception as e:
            return {
                "authentication_enabled": False,
                "status": "error",
                "error": str(e)
            }

    logger.info("✅ Authentication endpoints loaded successfully with lazy initialization")
    
except ImportError as e:
    logger.warning(f"⚠️  Authentication system not available: {e}")
    logger.info("📋 Service will run without authentication (backward compatibility)")
    
    # Add basic fallback endpoint
    @app.get("/api/v1/auth/status")
    async def auth_status_fallback():
        """Authentication system not available"""
        return {
            "authentication_enabled": False,
            "status": "not_configured",
            "message": "Authentication system not available in this deployment"
        }

# Export the enhanced app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)