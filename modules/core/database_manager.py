#!/usr/bin/env python3
"""
Database Manager module for AVA OLO Monitoring Dashboards
Handles database connections, pooling, and operations
"""
import psycopg2
import logging
from contextlib import contextmanager
from typing import Dict, Any, Optional
from .config import get_database_config

logger = logging.getLogger(__name__)

# Try to import connection pool
try:
    from database_pool import (
        init_connection_pool, get_db_session, get_db_connection as get_pool_connection,
        get_dashboard_metrics as get_pool_metrics, get_database_schema, test_connection_pool
    )
    POOL_AVAILABLE = True
except ImportError:
    POOL_AVAILABLE = False
    logger.warning("Connection pool not available, using direct connections")

class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self):
        self.config = get_database_config()
        self.pool_initialized = False
        
        if POOL_AVAILABLE:
            try:
                init_connection_pool()
                self.pool_initialized = True
                logger.info("Connection pool initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize connection pool: {e}")
    
    @contextmanager
    def get_connection(self):
        """Get a database connection (pooled or direct)"""
        if self.pool_initialized and POOL_AVAILABLE:
            # Use pooled connection
            try:
                with get_pool_connection() as conn:
                    yield conn
                return
            except Exception as e:
                logger.warning(f"Pool connection failed, falling back to direct: {e}")
        
        # Fall back to direct connection
        conn = None
        try:
            conn = self._create_direct_connection()
            yield conn
        finally:
            if conn:
                conn.close()
    
    def _create_direct_connection(self):
        """Create a direct database connection"""
        db_config = self.config
        
        if db_config['url']:
            return psycopg2.connect(db_config['url'])
        
        # Connect using individual parameters
        return psycopg2.connect(
            host=db_config['host'],
            database=db_config['name'],
            user=db_config['user'],
            password=db_config['password'],
            port=db_config['port']
        )
    
    def get_constitutional_db_connection(self):
        """Get a database connection following constitutional principles"""
        try:
            return self._create_direct_connection()
        except psycopg2.Error as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def test_connection(self):
        """Test database connectivity"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    result = cur.fetchone()
                    return result[0] == 1
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def execute_query(self, query: str, params: tuple = None):
        """Execute a query and return results"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    if cur.description:
                        columns = [desc[0] for desc in cur.description]
                        return {
                            'columns': columns,
                            'rows': cur.fetchall()
                        }
                    return {'affected_rows': cur.rowcount}
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def get_farmer_count(self) -> int:
        """Get total farmer count"""
        try:
            result = self.execute_query("SELECT COUNT(*) FROM farmers")
            return result['rows'][0][0] if result['rows'] else 0
        except Exception:
            return 0
    
    def get_total_hectares(self) -> float:
        """Get total hectares from all fields (restored from v2.2.3-verification-fix)"""
        try:
            # Try the working column names from July 19 version
            result = self.execute_query("SELECT COALESCE(SUM(area_ha), 0) FROM fields")
            if result['rows'] and result['rows'][0][0] > 0:
                return float(result['rows'][0][0])
            
            # Fallback to size_hectares column
            result = self.execute_query("SELECT COALESCE(SUM(size_hectares), 0) FROM fields")
            if result['rows']:
                return float(result['rows'][0][0])
            
            return 0.0
        except Exception as e:
            logger.warning(f"Failed to get hectares: {e}")
            return 0.0
    
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get metrics for dashboard display"""
        if self.pool_initialized and POOL_AVAILABLE:
            try:
                return get_pool_metrics()
            except Exception as e:
                logger.warning(f"Failed to get pool metrics: {e}")
        
        # Fall back to basic metrics
        return {
            'farmer_count': self.get_farmer_count(),
            'total_hectares': self.get_total_hectares(),
            'active_connections': 1 if self.test_connection() else 0,
            'pool_available': self.pool_initialized
        }

# Create singleton instance
_db_manager = None

def get_db_manager() -> DatabaseManager:
    """Get or create database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager

# Export convenience functions
def get_db_connection():
    """Get a database connection context manager"""
    return get_db_manager().get_connection()

def test_db_connection():
    """Test database connectivity"""
    return get_db_manager().test_connection()

def execute_db_query(query: str, params: tuple = None):
    """Execute a database query"""
    return get_db_manager().execute_query(query, params)