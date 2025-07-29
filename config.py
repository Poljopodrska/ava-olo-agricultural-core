"""
AVA OLO Dashboard System Configuration
Enhanced configuration for monitoring and database explorer
"""
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database Configuration - SINGLE SOURCE OF TRUTH
DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "ava_olo"),
    "username": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD")  # Required from environment
}

# Single PostgreSQL Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{DATABASE_CONFIG['username']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"
)

# Async PostgreSQL URL for async operations
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Connection Pool Settings
DB_POOL_SETTINGS = {
    "pool_size": int(os.getenv("DB_POOL_SIZE", "20")),
    "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "30")),
    "pool_pre_ping": True,
    "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "300"))
}

# API Configuration
API_CONFIG = {
    "monitoring_port": int(os.getenv("MONITORING_API_PORT", "8000")),
    "explorer_port": int(os.getenv("EXPLORER_API_PORT", "8001")),
    "dashboard_port": int(os.getenv("DASHBOARD_HTTP_PORT", "8080")),
    "secret_key": os.getenv("API_SECRET_KEY", "your-secret-key-change-in-production"),
    "cors_origins": os.getenv("CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080").split(","),
    "rate_limit": int(os.getenv("API_RATE_LIMIT", "100"))
}

# Twilio WhatsApp Configuration
TWILIO_CONFIG = {
    "account_sid": os.getenv("TWILIO_ACCOUNT_SID"),
    "auth_token": os.getenv("TWILIO_AUTH_TOKEN"),
    "whatsapp_number": os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+385919857451"),  # Croatian WhatsApp number
    "webhook_url": os.getenv("TWILIO_WEBHOOK_URL"),  # Public URL for webhook
    "enabled": bool(os.getenv("TWILIO_ENABLED", "false").lower() == "true")
}

# For direct access in webhook handler
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+385919857451')
BASE_URL = os.getenv('BASE_URL', 'http://ava-olo-alb-65365776.us-east-1.elb.amazonaws.com')

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

# Development Settings
DEV_CONFIG = {
    "debug": os.getenv("DEBUG", "False").lower() == "true",
    "auto_reload": os.getenv("AUTO_RELOAD", "False").lower() == "true",
    "open_browser": os.getenv("OPEN_BROWSER", "True").lower() == "true"
}

# Security Settings
SECURITY_CONFIG = {
    "https_only": os.getenv("HTTPS_ONLY", "False").lower() == "true",
    "secure_cookies": os.getenv("SECURE_COOKIES", "False").lower() == "true",
    "csrf_protection": os.getenv("CSRF_PROTECTION", "False").lower() == "true"
}

# External API Keys (optional)
EXTERNAL_APIS = {
    "weather_api_key": os.getenv("WEATHER_API_KEY"),
    "market_data_api_key": os.getenv("MARKET_DATA_API_KEY")
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

def validate_config():
    """Validate configuration settings"""
    errors = []
    
    # Check database configuration
    if not DATABASE_URL.startswith("postgresql://"):
        errors.append("❌ Only PostgreSQL connections allowed")
    
    # Check required environment variables
    required_vars = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"❌ Missing required environment variable: {var}")
    
    if errors:
        for error in errors:
            print(error)
        print("⚠️  Please copy env_example.txt to .env and configure properly")
        return False
    
    return True

# Initialize logging
setup_logging()

# Validate configuration on import
if validate_config():
    print(f"✅ Database Config: PostgreSQL at {DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}")
    print(f"✅ API Ports: Monitoring={API_CONFIG['monitoring_port']}, Explorer={API_CONFIG['explorer_port']}, Dashboard={API_CONFIG['dashboard_port']}")
    print(f"✅ Locale: {LOCALIZATION['timezone']} ({LOCALIZATION['locale']})")
else:
    print("⚠️  Configuration validation failed")