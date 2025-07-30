"""
AVA OLO Secure Configuration with AWS Secrets Manager
Enhanced configuration using AWS Secrets Manager for secure credential management
"""
import os
import logging
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables
load_dotenv()

# Try to import secrets manager utility
try:
    from utils.secrets_manager import get_database_config, get_admin_config, SecretsManager
    SECRETS_MANAGER_AVAILABLE = True
except ImportError:
    SECRETS_MANAGER_AVAILABLE = False
    logging.warning("⚠️ AWS Secrets Manager utility not available, using environment variables")

def get_secure_database_config() -> Dict[str, str]:
    """Get database configuration from AWS Secrets Manager or env vars"""
    if SECRETS_MANAGER_AVAILABLE and os.getenv('USE_SECRETS_MANAGER', 'false').lower() == 'true':
        try:
            return get_database_config()
        except Exception as e:
            logging.error(f"Failed to get database config from Secrets Manager: {e}")
    
    # Fallback to environment variables
    return {
        "DB_HOST": os.getenv("DB_HOST", "localhost"),
        "DB_PORT": os.getenv("DB_PORT", "5432"),
        "DB_NAME": os.getenv("DB_NAME", "ava_olo"),
        "DB_USER": os.getenv("DB_USER", "postgres"),
        "DB_PASSWORD": os.getenv("DB_PASSWORD", "your_password"),
        "DB_SSL_MODE": os.getenv("DB_SSL_MODE", "require")
    }

def get_secure_admin_config() -> Dict[str, str]:
    """Get admin configuration from AWS Secrets Manager or env vars"""
    if SECRETS_MANAGER_AVAILABLE and os.getenv('USE_SECRETS_MANAGER', 'false').lower() == 'true':
        try:
            return get_admin_config()
        except Exception as e:
            logging.error(f"Failed to get admin config from Secrets Manager: {e}")
    
    # Fallback to environment variables
    return {
        "ADMIN_USERNAME": os.getenv('ADMIN_USERNAME', 'admin'),
        "ADMIN_PASSWORD": os.getenv('ADMIN_PASSWORD', ''),
        "ADMIN_PASSWORD_HASH": os.getenv('ADMIN_PASSWORD_HASH', '')
    }

# Get secure configurations
DATABASE_CONFIG = get_secure_database_config()
ADMIN_CONFIG = get_secure_admin_config()

# Build secure database URL with SSL
DATABASE_URL = f"postgresql://{DATABASE_CONFIG['DB_USER']}:{DATABASE_CONFIG['DB_PASSWORD']}@{DATABASE_CONFIG['DB_HOST']}:{DATABASE_CONFIG['DB_PORT']}/{DATABASE_CONFIG['DB_NAME']}?sslmode={DATABASE_CONFIG['DB_SSL_MODE']}"

# Async PostgreSQL URL for async operations
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Connection Pool Settings with SSL
DB_POOL_SETTINGS = {
    "pool_size": int(os.getenv("DB_POOL_SIZE", "20")),
    "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "30")),
    "pool_pre_ping": True,
    "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "300")),
    "connect_args": {
        "sslmode": DATABASE_CONFIG['DB_SSL_MODE'],
        "sslcert": os.getenv("DB_SSL_CERT"),
        "sslkey": os.getenv("DB_SSL_KEY"),
        "sslrootcert": os.getenv("DB_SSL_ROOT_CERT")
    } if DATABASE_CONFIG['DB_SSL_MODE'] != "disable" else {}
}

# API Configuration
API_CONFIG = {
    "monitoring_port": int(os.getenv("MONITORING_API_PORT", "8000")),
    "explorer_port": int(os.getenv("EXPLORER_API_PORT", "8001")),
    "dashboard_port": int(os.getenv("DASHBOARD_HTTP_PORT", "8080")),
    "secret_key": os.getenv("API_SECRET_KEY", "your-secret-key-change-in-production"),
    "cors_origins": os.getenv("CORS_ORIGINS", "https://ava-olo.hr").split(","),
    "rate_limit": int(os.getenv("API_RATE_LIMIT", "100"))
}

# Logging Configuration
LOG_CONFIG = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "file": os.getenv("LOG_FILE", "ava_dashboard.log"),
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
}

# Croatian Localization
LOCALIZATION = {
    "timezone": os.getenv("TIMEZONE", "Europe/Zagreb"),
    "locale": os.getenv("LOCALE", "hr_HR.UTF-8"),
    "language": "hr",
    "currency": "EUR"
}

# Security Settings
SECURITY_CONFIG = {
    "https_only": os.getenv("HTTPS_ONLY", "True").lower() == "true",
    "secure_cookies": os.getenv("SECURE_COOKIES", "True").lower() == "true",
    "csrf_protection": os.getenv("CSRF_PROTECTION", "True").lower() == "true",
    "use_secrets_manager": os.getenv("USE_SECRETS_MANAGER", "false").lower() == "true",
    "session_timeout_hours": int(os.getenv("SESSION_TIMEOUT_HOURS", "8")),
    "max_login_attempts": int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
}

# Development Settings
DEV_CONFIG = {
    "debug": os.getenv("DEBUG", "False").lower() == "true",
    "auto_reload": os.getenv("AUTO_RELOAD", "False").lower() == "true",
    "environment": os.getenv("ENVIRONMENT", "production"),
    "enable_dev_endpoints": os.getenv("ENVIRONMENT", "production") == "development"
}

def setup_logging():
    """Configure logging for the dashboard system"""
    logging.basicConfig(
        level=getattr(logging, LOG_CONFIG["level"]),
        format=LOG_CONFIG["format"],
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_CONFIG["file"]) if LOG_CONFIG["file"] else logging.NullHandler()
        ]
    )

def validate_secure_config():
    """Validate secure configuration settings"""
    errors = []
    
    # Check database configuration
    if not DATABASE_URL.startswith("postgresql://"):
        errors.append("❌ Only PostgreSQL connections allowed")
    
    # Check SSL mode
    if DATABASE_CONFIG['DB_SSL_MODE'] not in ['require', 'prefer', 'disable']:
        errors.append("❌ Invalid SSL mode. Use: require, prefer, or disable")
    
    # Check if running in production without secrets manager
    if (os.getenv("ENVIRONMENT") == "production" and 
        not SECURITY_CONFIG["use_secrets_manager"]):
        errors.append("⚠️ Running in production without AWS Secrets Manager")
    
    # Check admin credentials
    if not ADMIN_CONFIG.get("ADMIN_PASSWORD") and not ADMIN_CONFIG.get("ADMIN_PASSWORD_HASH"):
        errors.append("❌ No admin password configured")
    
    # Check HTTPS in production
    if (os.getenv("ENVIRONMENT") == "production" and 
        not SECURITY_CONFIG["https_only"]):
        errors.append("⚠️ HTTPS not enforced in production")
    
    if errors:
        for error in errors:
            print(error)
        return False
    
    return True

def get_connection_string() -> str:
    """Get secure database connection string"""
    return DATABASE_URL

def mask_sensitive_info(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Mask sensitive information for logging"""
    masked = config_dict.copy()
    sensitive_keys = ['password', 'secret', 'key', 'token']
    
    for key, value in masked.items():
        if any(sens in key.lower() for sens in sensitive_keys):
            if isinstance(value, str) and value:
                masked[key] = f"{value[:4]}***{value[-4:]}" if len(value) > 8 else "***"
    
    return masked

# Initialize logging
setup_logging()

# Validate configuration on import
if validate_secure_config():
    masked_db_config = mask_sensitive_info(DATABASE_CONFIG)
    print(f"✅ Secure Database Config: PostgreSQL at {masked_db_config['DB_HOST']}:{masked_db_config['DB_PORT']}/{masked_db_config['DB_NAME']}")
    print(f"✅ SSL Mode: {DATABASE_CONFIG['DB_SSL_MODE']}")
    print(f"✅ Secrets Manager: {'Enabled' if SECURITY_CONFIG['use_secrets_manager'] else 'Disabled'}")
    print(f"✅ Environment: {DEV_CONFIG['environment']}")
else:
    print("⚠️  Security configuration validation failed")

# Export commonly used configurations
__all__ = [
    'DATABASE_URL',
    'ASYNC_DATABASE_URL', 
    'DB_POOL_SETTINGS',
    'API_CONFIG',
    'SECURITY_CONFIG',
    'ADMIN_CONFIG',
    'get_connection_string',
    'validate_secure_config'
]