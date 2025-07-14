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
    
    def __repr__(self):
        return f"<Config: {self.app_env} - DB: {self.db_host}>"

# Create singleton instance
config = Config()

# For backward compatibility
DATABASE_URL = config.database_url