#!/usr/bin/env python3
"""
Simplified database connection for field operations
"""
import psycopg2
import logging
from .config import get_database_config

logger = logging.getLogger(__name__)

def execute_simple_query(query: str, params: tuple = None):
    """Execute a query with simple error handling"""
    conn = None
    cursor = None
    
    try:
        # Get database config
        db_config = get_database_config()
        
        # Create connection
        if db_config['url']:
            conn = psycopg2.connect(db_config['url'])
        else:
            conn = psycopg2.connect(
                host=db_config['host'],
                database=db_config['name'],
                user=db_config['user'],
                password=db_config['password'],
                port=db_config['port']
            )
        
        cursor = conn.cursor()
        
        # Execute query
        cursor.execute(query, params)
        
        # Check if this is a SELECT or RETURNING query
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            # Commit if it's an INSERT/UPDATE/DELETE with RETURNING
            if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                conn.commit()
            
            return {
                'success': True,
                'columns': columns,
                'rows': rows
            }
        else:
            # Commit for INSERT/UPDATE/DELETE without RETURNING
            conn.commit()
            return {
                'success': True,
                'affected_rows': cursor.rowcount
            }
            
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        logger.error(f"Query was: {query}")
        logger.error(f"Params were: {params}")
        
        if conn:
            try:
                conn.rollback()
            except:
                pass
        
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass