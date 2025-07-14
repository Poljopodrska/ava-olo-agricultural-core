"""
Constitutional Config Manager
Provides configuration for AVA OLO Agricultural Core
Emergency fix for startup failure
"""
import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv

# Setup logging for debug
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Debug: Print that config manager is loading
logger.info("🏛️ Loading Constitutional Config Manager...")

class Config:
    """Configuration class with all required settings"""
    
    # Database settings
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = int(os.getenv('DB_PORT', '5432'))
    db_name = os.getenv('DB_NAME', 'farmer_crm')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    
    # Build database URL
    database_url = os.getenv('DATABASE_URL', 
        f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )
    
    # OpenAI settings
    openai_api_key = os.getenv('OPENAI_API_KEY', '')
    openai_model = os.getenv('OPENAI_MODEL', 'gpt-4')
    openai_temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
    
    # External APIs
    perplexity_api_key = os.getenv('PERPLEXITY_API_KEY', '')
    
    # Application settings
    app_env = os.getenv('APP_ENV', 'development')
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    # Constitutional compliance settings
    enable_constitutional_checks = os.getenv('ENABLE_CONSTITUTIONAL_CHECKS', 'true').lower() == 'true'
    
    # Additional properties for compatibility
    DATABASE_URL = property(lambda self: self.database_url)
    DB_HOST = property(lambda self: self.db_host)
    DB_NAME = property(lambda self: self.db_name)
    DB_USER = property(lambda self: self.db_user)
    DB_PASSWORD = property(lambda self: self.db_password)
    DB_PORT = property(lambda self: str(self.db_port))
    OPENAI_API_KEY = property(lambda self: self.openai_api_key)
    
    def validate_constitutional_compliance(self):
        """Validate constitutional compliance settings"""
        return True  # Simplified for now
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return getattr(self, key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Return all config as dictionary"""
        return {
            'database_url': self.database_url,
            'app_env': self.app_env,
            'constitutional_compliance': {
                'checks_enabled': self.enable_constitutional_checks,
                'llm_first': True,
                'privacy_mode': True
            }
        }
    
    def __repr__(self):
        return f"<Config: {self.app_env} - DB: {self.db_host}>"

# Create singleton instance
try:
    config = Config()
    logger.info(f"✅ Config created: {config.app_env} environment")
    logger.info(f"✅ Database: {config.db_host}")
    logger.info(f"✅ Constitutional checks: {'enabled' if config.enable_constitutional_checks else 'disabled'}")
except Exception as e:
    logger.error(f"❌ Config creation failed: {e}")
    raise

# For backward compatibility
DATABASE_URL = config.database_url

# Constitutional compliance verification
logger.info("🏛️ Constitutional Config Manager loaded successfully")
logger.info(f"🎯 Ready for: Database operations, LLM processing, Constitutional compliance")