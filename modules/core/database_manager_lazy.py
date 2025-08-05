#!/usr/bin/env python3
"""
Database Manager module with LAZY initialization
Fixes the import-time database connection issue
"""
import psycopg2
import asyncpg
import logging
import time
from contextlib import contextmanager, asynccontextmanager
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
    """Manages database connections and operations with LAZY initialization"""
    
    def __init__(self):
        self.config = get_database_config()
        self.pool_initialized = False
        self.async_pool = None
        self._init_attempted = False
        
    def _ensure_pool(self):
        """Lazily initialize the connection pool on first use"""
        if not self._init_attempted and POOL_AVAILABLE:
            self._init_attempted = True
            try:
                init_connection_pool()
                self.pool_initialized = True
                logger.info("Connection pool initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize connection pool: {e}")
    
    @contextmanager
    def get_connection(self):
        """Get a database connection (pooled or direct)"""
        self._ensure_pool()  # Initialize pool on first use
        
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
            conn = psycopg2.connect(
                host=self.config['host'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password'],
                port=self.config['port']
            )
            yield conn
        finally:
            if conn:
                conn.close()
                
    def test_connection(self, retries=3, delay=1):
        """Test database connection"""
        self._ensure_pool()  # Initialize pool on first use
        
        if self.pool_initialized and POOL_AVAILABLE:
            try:
                return test_connection_pool()
            except:
                pass
                
        # Direct connection test
        for attempt in range(retries):
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    cursor.close()
                    return result[0] == 1
            except Exception as e:
                logger.warning(f"Connection test attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(delay)
        return False
    
    async def get_connection_async(self):
        """Get async database connection"""
        if not self.async_pool:
            try:
                self.async_pool = await asyncpg.create_pool(
                    host=self.config['host'],
                    database=self.config['database'],
                    user=self.config['user'],
                    password=self.config['password'],
                    port=self.config['port'],
                    min_size=1,
                    max_size=10
                )
            except Exception as e:
                logger.error(f"Failed to create async pool: {e}")
                raise
                
        return self.async_pool.acquire()
    
    def execute_query(self, query: str, params: tuple = None) -> Any:
        """Execute a query and return results"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                if query.strip().upper().startswith(('SELECT', 'WITH')):
                    return cursor.fetchall()
                else:
                    conn.commit()
                    return cursor.rowcount
            finally:
                cursor.close()

# Global instance - but won't connect until first use
_db_manager = None

def get_db_manager():
    """Get the global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager