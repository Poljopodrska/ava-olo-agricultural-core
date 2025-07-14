"""
Constitutional Authentication Middleware
FastAPI middleware for farm authentication and authorization

Constitutional compliance: Security-First, Privacy-First, Transparency-First
"""

from fastapi import HTTPException, Depends, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import logging
from functools import wraps
from .farm_auth import FarmAuthManager

logger = logging.getLogger(__name__)

# Security scheme for Swagger documentation
security = HTTPBearer()

class AuthMiddleware:
    """
    Constitutional authentication middleware for FastAPI
    
    Provides secure authentication and authorization for farm operations
    """
    
    def __init__(self, auth_manager: FarmAuthManager):
        self.auth_manager = auth_manager
    
    async def get_current_user(self, 
                              credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """
        FastAPI dependency to get current authenticated user
        
        Constitutional compliance: Security-First (proper token validation)
        """
        try:
            if not credentials or not credentials.credentials:
                raise HTTPException(
                    status_code=401, 
                    detail="Missing authorization token",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            token = credentials.credentials
            user_data = self.auth_manager.verify_token(token)
            
            if not user_data:
                raise HTTPException(
                    status_code=401, 
                    detail="Invalid or expired token",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            return user_data
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Authentication service error"
            )
    
    async def get_optional_user(self, 
                               credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
        """
        FastAPI dependency for optional authentication
        
        Returns user data if authenticated, None otherwise
        """
        try:
            if not credentials or not credentials.credentials:
                return None
            
            token = credentials.credentials
            user_data = self.auth_manager.verify_token(token)
            
            return user_data
            
        except Exception as e:
            logger.warning(f"Optional authentication error: {e}")
            return None
    
    def require_farm_access(self, required_farmer_id: int, current_user: Dict[str, Any]) -> bool:
        """
        Verify user has access to specific farm data
        
        Constitutional compliance: Privacy-First (data isolation between farms)
        """
        if current_user['farmer_id'] != required_farmer_id:
            raise HTTPException(
                status_code=403, 
                detail="Access denied to this farm data"
            )
        
        return True
    
    def require_role(self, required_roles: list, current_user: Dict[str, Any]) -> bool:
        """
        Verify user has required role
        
        Constitutional compliance: Security-First (role-based access control)
        """
        user_role = current_user.get('role', 'member')
        
        if user_role not in required_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required role: {required_roles}, your role: {user_role}"
            )
        
        return True
    
    def require_permission(self, permission: str, current_user: Dict[str, Any]) -> bool:
        """
        Verify user has specific permission
        
        Constitutional compliance: Security-First (permission-based access)
        """
        try:
            user_permissions = self.auth_manager.get_user_permissions(current_user['user_id'])
            
            if not user_permissions.get(permission, False):
                raise HTTPException(
                    status_code=403,
                    detail=f"Access denied. Missing permission: {permission}"
                )
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Permission check error: {e}")
            raise HTTPException(
                status_code=500,
                detail="Permission service error"
            )
    
    async def audit_action(self, 
                          action_type: str, 
                          table_name: str, 
                          record_id: int, 
                          current_user: Dict[str, Any],
                          old_values: Dict = None, 
                          new_values: Dict = None,
                          description: str = None):
        """
        Helper to log audited actions
        
        Constitutional compliance: Transparency-First (complete audit trail)
        """
        try:
            self.auth_manager.log_activity(
                farmer_id=current_user['farmer_id'],
                user_id=current_user['user_id'],
                action_type=action_type,
                table_name=table_name,
                record_id=record_id,
                old_values=old_values,
                new_values=new_values,
                description=description
            )
            
        except Exception as e:
            logger.error(f"Audit logging error: {e}")
            # Don't raise exception - audit failures shouldn't break main functionality
    
    async def get_farm_context(self, current_user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get farm context for the current user
        
        Constitutional compliance: MANGO Rule (works for any farm globally)
        """
        try:
            return {
                'farmer_id': current_user['farmer_id'],
                'farm_name': current_user['farm_name'],
                'user_name': current_user['user_name'],
                'user_role': current_user['role'],
                'country': current_user.get('country', 'Unknown'),
                'wa_phone': current_user['wa_phone']
            }
            
        except Exception as e:
            logger.error(f"Error getting farm context: {e}")
            return {}


# Dependency functions for common auth patterns
class AuthDependencies:
    """
    Common authentication dependency functions
    """
    
    def __init__(self, auth_middleware: AuthMiddleware):
        self.auth_middleware = auth_middleware
    
    def current_user(self):
        """Get current authenticated user"""
        return Depends(self.auth_middleware.get_current_user)
    
    def optional_user(self):
        """Get optional authenticated user"""
        return Depends(self.auth_middleware.get_optional_user)
    
    def farm_owner(self):
        """Require farm owner role"""
        def _check_owner(current_user: Dict[str, Any] = Depends(self.auth_middleware.get_current_user)):
            self.auth_middleware.require_role(['owner'], current_user)
            return current_user
        return Depends(_check_owner)
    
    def farm_member(self):
        """Require farm member role or higher"""
        def _check_member(current_user: Dict[str, Any] = Depends(self.auth_middleware.get_current_user)):
            self.auth_middleware.require_role(['owner', 'member'], current_user)
            return current_user
        return Depends(_check_member)
    
    def can_add_users(self):
        """Require permission to add users"""
        def _check_permission(current_user: Dict[str, Any] = Depends(self.auth_middleware.get_current_user)):
            self.auth_middleware.require_permission('can_add_users', current_user)
            return current_user
        return Depends(_check_permission)
    
    def can_modify_tasks(self):
        """Require permission to modify tasks"""
        def _check_permission(current_user: Dict[str, Any] = Depends(self.auth_middleware.get_current_user)):
            self.auth_middleware.require_permission('can_modify_tasks', current_user)
            return current_user
        return Depends(_check_permission)
    
    def can_modify_inventory(self):
        """Require permission to modify inventory"""
        def _check_permission(current_user: Dict[str, Any] = Depends(self.auth_middleware.get_current_user)):
            self.auth_middleware.require_permission('can_modify_inventory', current_user)
            return current_user
        return Depends(_check_permission)
    
    def can_view_activity_log(self):
        """Require permission to view activity log"""
        def _check_permission(current_user: Dict[str, Any] = Depends(self.auth_middleware.get_current_user)):
            self.auth_middleware.require_permission('can_view_activity_log', current_user)
            return current_user
        return Depends(_check_permission)


# Decorators for method-level authentication
def require_auth(func):
    """
    Decorator to require authentication for a function
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # This decorator would need to be adapted based on your specific use case
        # For FastAPI, it's better to use Depends() in the route definition
        return await func(*args, **kwargs)
    return wrapper


def require_farm_owner(func):
    """
    Decorator to require farm owner role
    """
    @wraps(func)
    async def wrapper(current_user: Dict[str, Any], *args, **kwargs):
        if current_user.get('role') != 'owner':
            raise HTTPException(status_code=403, detail="Farm owner access required")
        return await func(current_user, *args, **kwargs)
    return wrapper


# Custom exception classes for authentication errors
class AuthenticationError(HTTPException):
    """Custom authentication error"""
    def __init__(self, detail: str = "Authentication required"):
        super().__init__(status_code=401, detail=detail)


class AuthorizationError(HTTPException):
    """Custom authorization error"""
    def __init__(self, detail: str = "Access denied"):
        super().__init__(status_code=403, detail=detail)


class FarmAccessError(HTTPException):
    """Custom farm access error"""
    def __init__(self, detail: str = "Access denied to this farm"):
        super().__init__(status_code=403, detail=detail)