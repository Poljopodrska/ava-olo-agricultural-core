"""
Database Operations - Migrated to use Constitutional Config Manager
This shows how to update existing database operations to use centralized config
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, date
from decimal import Decimal
import asyncpg
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import constitutional config manager instead of local config
try:
    from ava_olo_shared.config_manager import config
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ava-olo-shared'))
    from config_manager import config

logger = logging.getLogger(__name__)

# Default pool settings (can be moved to config)
DB_POOL_SETTINGS = {
    'pool_size': 10,
    'max_overflow': 20,
    'pool_pre_ping': True,
    'pool_recycle': 3600
}


class DatabaseOperations:
    """
    Database operations using constitutional config manager
    Migrated from hardcoded environment variables
    """
    
    def __init__(self, connection_string: str = None):
        # Use config manager instead of local DATABASE_URL
        self.connection_string = connection_string or config.database_url
        
        # Ensure PostgreSQL only (Constitutional requirement)
        assert self.connection_string.startswith("postgresql://"), "❌ Only PostgreSQL connections allowed"
        
        # Log config source for transparency
        logger.info(f"Database configuration loaded from: {config.get_config_dict()['env_file']}")
        
        # For WSL2 to Windows connection, we might need to adjust the connection
        if "host.docker.internal" in self.connection_string:
            # This is correct for WSL2 to Windows connection
            pass
        
        self.engine = create_engine(
            self.connection_string,
            **DB_POOL_SETTINGS
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Log constitutional compliance if enabled
        if config.enable_constitutional_checks:
            compliance = config.validate_constitutional_compliance()
            if not compliance['postgresql_only']:
                logger.error("Constitutional violation: Non-PostgreSQL database detected!")
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    async def get_farmer_info(self, farmer_id: int) -> Optional[Dict[str, Any]]:
        """Get farmer information by ID"""
        try:
            with self.get_session() as session:
                # Note: In full constitutional compliance, this would use LLM
                # For now, keeping SQL but logging the violation
                if config.enable_constitutional_checks:
                    logger.warning("Constitutional violation: Hardcoded SQL detected. Should use LLM-first approach.")
                
                result = session.execute(
                    text("""
                    SELECT id, farm_name, manager_name, manager_last_name, 
                           city, wa_phone_number, country_code, preferred_language
                    FROM farmers 
                    WHERE id = :farmer_id
                    """),
                    {"farmer_id": farmer_id}
                ).fetchone()
                
                if result:
                    return {
                        "id": result[0],
                        "farm_name": result[1],
                        "manager_name": result[2],
                        "manager_last_name": result[3],
                        "city": result[4],
                        "wa_phone_number": result[5],
                        "country_code": result[6] if len(result) > 6 else None,
                        "preferred_language": result[7] if len(result) > 7 else config.default_language
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error getting farmer info: {str(e)}")
            return None
    
    async def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            with self.get_session() as session:
                result = session.execute(text("SELECT COUNT(*) FROM farmers"))
                count = result.scalar()
                
                # Log using config manager's log level
                if config.log_level == 'DEBUG':
                    logger.debug(f"Detailed health check: {count} farmers, compliance: {config.validate_constitutional_compliance()}")
                else:
                    logger.info(f"Database health check: Connected with {count} farmers")
                
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False
    
    # Additional methods would follow the same pattern...


# Example of how to check feature flags
def get_database_operations():
    """Get appropriate database operations based on feature flags"""
    if config.enable_llm_first:
        # Import and use constitutional version
        logger.info("Using LLM-first database operations (Constitutional compliance)")
        from database_operations_constitutional import DatabaseOperations as ConstitutionalDB
        return ConstitutionalDB()
    else:
        # Use traditional version but log warning
        logger.warning("Using traditional database operations (Constitutional violation)")
        return DatabaseOperations()


# Migration helper
def migrate_to_constitutional():
    """Helper to migrate to constitutional compliance"""
    print("Migration Guide:")
    print("1. Replace all os.getenv() calls with config properties")
    print("2. Replace load_dotenv() with config manager import")
    print("3. Enable LLM-first mode: ENABLE_LLM_FIRST=true")
    print(f"4. Current compliance: {config.validate_constitutional_compliance()}")
    
    # Show current configuration
    print("\nCurrent Configuration:")
    for key, value in config.get_config_dict().items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    # Test configuration
    print("Testing database configuration...")
    db_ops = DatabaseOperations()
    
    # Run health check
    import asyncio
    result = asyncio.run(db_ops.health_check())
    print(f"Health check: {'✓ PASSED' if result else '✗ FAILED'}")
    
    # Show migration guide
    migrate_to_constitutional()