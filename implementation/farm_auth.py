"""
Constitutional Farm Authentication Manager
Multi-user authentication system for AVA OLO farms

Constitutional compliance: MANGO Rule, Privacy-First, LLM-First
"""

import bcrypt
import jwt
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import os
import logging

logger = logging.getLogger(__name__)

class FarmAuthManager:
    """
    Constitutional farm authentication manager
    
    Supports multiple family members accessing the same farm data
    with full audit trails and constitutional compliance
    """
    
    def __init__(self, db_config: Dict[str, Any] = None):
        """Initialize authentication manager"""
        self.db_config = db_config or self._get_db_config()
        # Get JWT secret from Secrets Manager or environment
        try:
            from .secrets_manager import get_jwt_secret
            self.jwt_secret = get_jwt_secret()
        except ImportError:
            self.jwt_secret = os.getenv('JWT_SECRET', 'constitutional-farm-secret-key-change-in-production')
        self.jwt_expiry_hours = int(os.getenv('JWT_EXPIRY_HOURS', '24'))
        self.connection = None
        
    def _get_db_config(self) -> Dict[str, Any]:
        """Get database configuration from Secrets Manager or environment"""
        try:
            from .secrets_manager import get_database_config
            return get_database_config()
        except ImportError:
            # Fallback if secrets_manager not available
            logger.warning("Secrets manager not available, using aurora_connection_fix")
            from .aurora_connection_fix import get_aurora_config
            return get_aurora_config()
    
    def _get_connection(self):
        """Get database connection with retry logic (same as dashboards)"""
        if self.connection and not self.connection.closed:
            return self.connection
        
        # First try without SSL mode specified (like LLM engine)
        try:
            self.connection = psycopg2.connect(
                host=self.db_config['host'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                port=self.db_config['port'],
                connect_timeout=10,
                cursor_factory=RealDictCursor
            )
            logger.info("Connected to Aurora (default SSL mode)")
            return self.connection
        except Exception as e:
            logger.warning(f"Default connection failed: {e}")
        
        # Then try different SSL modes in order of preference
        ssl_modes = ['prefer', 'disable', 'require']
        
        for ssl_mode in ssl_modes:
            try:
                self.connection = psycopg2.connect(
                    host=self.db_config['host'],
                    database=self.db_config['database'],
                    user=self.db_config['user'],
                    password=self.db_config['password'],
                    port=self.db_config['port'],
                    connect_timeout=10,
                    sslmode=ssl_mode,
                    cursor_factory=RealDictCursor
                )
                logger.info(f"Connected to Aurora with SSL mode: {ssl_mode}")
                return self.connection
                
            except psycopg2.OperationalError as e:
                if "SSL" in str(e) or "ssl" in str(e):
                    logger.warning(f"SSL mode {ssl_mode} failed, trying next...")
                    continue
                else:
                    logger.warning(f"Connection failed with {ssl_mode}: {e}")
                    continue
                    
        raise Exception("Failed to connect to database with all SSL modes")
    
    def close_connection(self):
        """Close database connection"""
        if self.connection and not self.connection.closed:
            self.connection.close()
            self.connection = None
    
    def register_farm_user(self, farmer_id: int, wa_phone: str, 
                          password: str, user_name: str, 
                          role: str = 'member', created_by_user_id: int = None) -> Dict[str, Any]:
        """
        Register new family member for farm access
        
        Constitutional compliance: MANGO Rule (works for any country)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Hash password using bcrypt
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Insert new farm user
            cursor.execute("""
                INSERT INTO farm_users (farmer_id, wa_phone_number, password_hash, 
                                       user_name, role, created_by_user_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, farmer_id, wa_phone_number, user_name, role, created_at
            """, (farmer_id, wa_phone, password_hash, user_name, role, created_by_user_id))
            
            result = cursor.fetchone()
            conn.commit()
            
            # Log the registration
            self.log_activity(
                farmer_id=farmer_id,
                user_id=created_by_user_id or result['id'],
                action_type='created',
                table_name='farm_users',
                record_id=result['id'],
                description=f"Added new family member: {user_name} ({role})"
            )
            
            logger.info(f"Successfully registered farm user: {user_name} for farmer {farmer_id}")
            return dict(result)
            
        except psycopg2.IntegrityError as e:
            if "wa_phone_number" in str(e):
                raise ValueError(f"WhatsApp number {wa_phone} is already registered")
            raise e
        except Exception as e:
            logger.error(f"Error registering farm user: {e}")
            raise e
    
    def authenticate_user(self, wa_phone: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user and return access token
        
        Constitutional compliance: Privacy-First (secure password handling)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Find user by WhatsApp phone
            cursor.execute("""
                SELECT fu.*, f.farm_name, f.manager_name as farm_owner_name, f.country
                FROM farm_users fu
                JOIN farmers f ON fu.farmer_id = f.id  
                WHERE fu.wa_phone_number = %s AND fu.is_active = true
            """, (wa_phone,))
            
            user = cursor.fetchone()
            if not user:
                logger.warning(f"Authentication failed: WhatsApp number {wa_phone} not found")
                return None
            
            # Verify password
            if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                logger.warning(f"Authentication failed: Invalid password for {wa_phone}")
                return None
            
            # Update last login
            cursor.execute("""
                UPDATE farm_users SET last_login = NOW() WHERE id = %s
            """, (user['id'],))
            conn.commit()
            
            # Generate JWT token
            token_payload = {
                'user_id': user['id'],
                'farmer_id': user['farmer_id'],
                'user_name': user['user_name'],
                'farm_name': user['farm_name'],
                'role': user['role'],
                'wa_phone': user['wa_phone_number'],
                'country': user['country'],  # MANGO Rule compliance
                'exp': datetime.utcnow() + timedelta(hours=self.jwt_expiry_hours)
            }
            
            token = jwt.encode(token_payload, self.jwt_secret, algorithm='HS256')
            
            # Log successful authentication
            self.log_activity(
                farmer_id=user['farmer_id'],
                user_id=user['id'],
                action_type='login',
                table_name='farm_users',
                record_id=user['id'],
                description=f"Successful login from {wa_phone}"
            )
            
            logger.info(f"Successfully authenticated user: {user['user_name']} ({wa_phone})")
            
            return {
                'token': token,
                'user': {
                    'id': user['id'],
                    'farmer_id': user['farmer_id'],
                    'user_name': user['user_name'],
                    'farm_name': user['farm_name'],
                    'role': user['role'],
                    'wa_phone': user['wa_phone_number'],
                    'country': user['country']
                }
            }
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token and return user info
        
        Constitutional compliance: Security-First (proper token validation)
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            
            # Verify user still exists and is active
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT is_active FROM farm_users WHERE id = %s
            """, (payload['user_id'],))
            
            user = cursor.fetchone()
            if not user or not user['is_active']:
                logger.warning(f"Token verification failed: User {payload['user_id']} not found or inactive")
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token verification failed: Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Token verification failed: Invalid token")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None
    
    def get_farm_family_members(self, farmer_id: int) -> List[Dict[str, Any]]:
        """
        Get all family members who have access to this farm
        
        Constitutional compliance: Privacy-First (only farm data, no passwords)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, user_name, wa_phone_number, role, is_active, 
                       created_at, last_login,
                       (SELECT user_name FROM farm_users WHERE id = fu.created_by_user_id) as created_by
                FROM farm_users fu
                WHERE farmer_id = %s 
                ORDER BY role DESC, created_at ASC
            """, (farmer_id,))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error getting farm family members: {e}")
            return []
    
    def get_farm_activity_log(self, farmer_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent farm activity log (who did what)
        
        Constitutional compliance: Transparency-First (full audit trail)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT fal.*, fu.user_name, fu.wa_phone_number
                FROM farm_activity_log fal
                JOIN farm_users fu ON fal.user_id = fu.id
                WHERE fal.farmer_id = %s
                ORDER BY fal.timestamp DESC
                LIMIT %s
            """, (farmer_id, limit))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error getting farm activity log: {e}")
            return []
    
    def log_activity(self, farmer_id: int, user_id: int, action_type: str,
                    table_name: str, record_id: int = None, 
                    old_values: Dict = None, new_values: Dict = None,
                    description: str = None):
        """
        Log family farm activity for audit trail
        
        Constitutional compliance: Transparency-First (complete audit trail)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO farm_activity_log 
                (farmer_id, user_id, action_type, table_name, record_id, 
                 old_values, new_values, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (farmer_id, user_id, action_type, table_name, record_id,
                  old_values, new_values, description))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
            # Don't raise exception for logging errors - shouldn't break main functionality
    
    def deactivate_user(self, user_id: int, deactivated_by_user_id: int) -> bool:
        """
        Deactivate a farm user (soft delete)
        
        Constitutional compliance: Privacy-First (soft delete, audit trail)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get user info before deactivation
            cursor.execute("""
                SELECT farmer_id, user_name FROM farm_users WHERE id = %s
            """, (user_id,))
            
            user = cursor.fetchone()
            if not user:
                return False
            
            # Deactivate user
            cursor.execute("""
                UPDATE farm_users SET is_active = false WHERE id = %s
            """, (user_id,))
            
            conn.commit()
            
            # Log the deactivation
            self.log_activity(
                farmer_id=user['farmer_id'],
                user_id=deactivated_by_user_id,
                action_type='deactivated',
                table_name='farm_users',
                record_id=user_id,
                description=f"Deactivated farm user: {user['user_name']}"
            )
            
            logger.info(f"Successfully deactivated user: {user['user_name']} (ID: {user_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error deactivating user: {e}")
            return False
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """
        Change user password with verification
        
        Constitutional compliance: Security-First (password verification)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get current password hash
            cursor.execute("""
                SELECT password_hash, farmer_id, user_name FROM farm_users WHERE id = %s
            """, (user_id,))
            
            user = cursor.fetchone()
            if not user:
                return False
            
            # Verify old password
            if not bcrypt.checkpw(old_password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                logger.warning(f"Password change failed: Invalid old password for user {user_id}")
                return False
            
            # Hash new password
            new_password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Update password
            cursor.execute("""
                UPDATE farm_users SET password_hash = %s WHERE id = %s
            """, (new_password_hash, user_id))
            
            conn.commit()
            
            # Log password change
            self.log_activity(
                farmer_id=user['farmer_id'],
                user_id=user_id,
                action_type='password_changed',
                table_name='farm_users',
                record_id=user_id,
                description=f"Password changed for user: {user['user_name']}"
            )
            
            logger.info(f"Successfully changed password for user: {user['user_name']} (ID: {user_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error changing password: {e}")
            return False
    
    def get_user_permissions(self, user_id: int) -> Dict[str, bool]:
        """
        Get user permissions based on role
        
        Constitutional compliance: Security-First (role-based access)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT role FROM farm_users WHERE id = %s AND is_active = true
            """, (user_id,))
            
            user = cursor.fetchone()
            if not user:
                return {}
            
            role = user['role']
            
            # Define permissions based on role
            permissions = {
                'owner': {
                    'can_add_users': True,
                    'can_remove_users': True,
                    'can_modify_tasks': True,
                    'can_modify_inventory': True,
                    'can_view_activity_log': True,
                    'can_change_farm_settings': True
                },
                'member': {
                    'can_add_users': False,
                    'can_remove_users': False,
                    'can_modify_tasks': True,
                    'can_modify_inventory': True,
                    'can_view_activity_log': True,
                    'can_change_farm_settings': False
                },
                'worker': {
                    'can_add_users': False,
                    'can_remove_users': False,
                    'can_modify_tasks': True,
                    'can_modify_inventory': False,
                    'can_view_activity_log': False,
                    'can_change_farm_settings': False
                }
            }
            
            return permissions.get(role, {})
            
        except Exception as e:
            logger.error(f"Error getting user permissions: {e}")
            return {}
    
    def __del__(self):
        """Cleanup on destruction"""
        self.close_connection()