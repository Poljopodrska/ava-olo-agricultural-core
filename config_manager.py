"""
Config Manager for AVA OLO Agricultural Core
Simple configuration management for AWS deployment
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
    
    def __repr__(self):
        return f"<Config: {self.app_env} - DB: {self.db_host}>"

# Create singleton instance
config = Config()

# For backward compatibility
DATABASE_URL = config.database_url