#!/usr/bin/env python3
"""
High-Performance Database Connection Pool for Monitoring Dashboards
Implements persistent connections with SQLAlchemy for <1s response times
"""

import os
import logging
from sqlalchemy import create_engine, text, pool
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import time
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# Global engine and session factory
_engine = None
_session_factory = None

def init_connection_pool():
    """Initialize SQLAlchemy connection pool with VPC-optimized settings"""
    global _engine, _session_factory
    
    if _engine:
        return _engine
    
    # Build database URL
    db_host = os.getenv('DB_HOST', 'farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com')
    db_name = os.getenv('DB_NAME', 'postgres')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD')
    db_port = os.getenv('DB_PORT', '5432')
    
    database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    # Create engine with optimized pool settings
    _engine = create_engine(
        database_url,
        poolclass=pool.QueuePool,
        pool_size=5,  # 5 persistent connections
        max_overflow=5,  # Allow up to 10 total connections
        pool_timeout=3,  # 3 second timeout to get connection from pool
        pool_recycle=3600,  # Recycle connections after 1 hour
        pool_pre_ping=True,  # Test connections before using
        connect_args={
            "connect_timeout": 2,  # 2 second connection timeout for VPC
            "options": "-c statement_timeout=2000"  # 2 second query timeout
        }
    )
    
    # Create session factory
    _session_factory = sessionmaker(bind=_engine)
    
    logger.info("✅ SQLAlchemy connection pool initialized with 5-10 connections")
    return _engine

@contextmanager
def get_db_session():
    """Get a database session from the pool"""
    if not _session_factory:
        init_connection_pool()
    
    session = _session_factory()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        session.close()

@contextmanager
def get_db_connection():
    """Get a raw database connection from the pool (for legacy code)"""
    if not _engine:
        init_connection_pool()
    
    conn = _engine.raw_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()

def execute_query(query: str, params: Dict = None) -> List[Dict[str, Any]]:
    """Execute a query and return results as list of dicts with timing"""
    start_time = time.time()
    
    with get_db_session() as session:
        result = session.execute(text(query), params or {})
        
        # Convert to list of dicts
        columns = result.keys()
        rows = []
        for row in result:
            rows.append(dict(zip(columns, row)))
        
        execution_time = (time.time() - start_time) * 1000
        logger.debug(f"Query executed in {execution_time:.0f}ms: {query[:50]}...")
        
        return rows

def get_dashboard_metrics() -> Dict[str, Any]:
    """Get all dashboard metrics in a single optimized query"""
    query = """
    WITH metrics AS (
        SELECT 
            (SELECT COUNT(*) FROM farmers) as total_farmers,
            (SELECT COUNT(*) FROM fields) as total_fields,
            (SELECT COALESCE(SUM(area_ha), 0) FROM fields) as total_hectares,
            (SELECT COUNT(*) FROM farmers WHERE created_at >= NOW() - INTERVAL '24 hours') as farmers_24h,
            (SELECT COUNT(*) FROM farmers WHERE created_at >= NOW() - INTERVAL '7 days') as farmers_7d,
            (SELECT COUNT(*) FROM farmers WHERE created_at >= NOW() - INTERVAL '30 days') as farmers_30d
    )
    SELECT * FROM metrics
    """
    
    start_time = time.time()
    result = execute_query(query)
    execution_time = (time.time() - start_time) * 1000
    
    metrics = result[0] if result else {
        'total_farmers': 0,
        'total_fields': 0,
        'total_hectares': 0,
        'farmers_24h': 0,
        'farmers_7d': 0,
        'farmers_30d': 0
    }
    
    metrics['query_time_ms'] = execution_time
    return metrics

def get_database_schema() -> Dict[str, List[Dict[str, Any]]]:
    """Get complete database schema information"""
    query = """
    SELECT 
        t.table_name,
        c.column_name,
        c.data_type,
        c.character_maximum_length,
        c.is_nullable,
        c.column_default,
        CASE 
            WHEN pk.column_name IS NOT NULL THEN 'PRIMARY KEY'
            WHEN fk.column_name IS NOT NULL THEN 'FOREIGN KEY'
            ELSE NULL
        END as constraint_type,
        fk.foreign_table_name,
        fk.foreign_column_name
    FROM information_schema.tables t
    JOIN information_schema.columns c ON t.table_name = c.table_name
    LEFT JOIN (
        SELECT ku.table_name, ku.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage ku 
            ON tc.constraint_name = ku.constraint_name
        WHERE tc.constraint_type = 'PRIMARY KEY'
    ) pk ON c.table_name = pk.table_name AND c.column_name = pk.column_name
    LEFT JOIN (
        SELECT 
            kcu.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu 
            ON tc.constraint_name = ccu.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
    ) fk ON c.table_name = fk.table_name AND c.column_name = fk.column_name
    WHERE t.table_schema = 'public'
    ORDER BY t.table_name, c.ordinal_position
    """
    
    rows = execute_query(query)
    
    # Group by table
    schema = {}
    for row in rows:
        table_name = row['table_name']
        if table_name not in schema:
            schema[table_name] = []
        
        schema[table_name].append({
            'column_name': row['column_name'],
            'data_type': row['data_type'],
            'max_length': row['character_maximum_length'],
            'nullable': row['is_nullable'] == 'YES',
            'default': row['column_default'],
            'constraint': row['constraint_type'],
            'references': f"{row['foreign_table_name']}.{row['foreign_column_name']}" 
                if row['foreign_table_name'] else None
        })
    
    return schema

def test_connection_pool() -> Dict[str, Any]:
    """Test connection pool performance"""
    results = {
        'pool_initialized': _engine is not None,
        'pool_size': _engine.pool.size() if _engine else 0,
        'pool_checked_out': _engine.pool.checkedout() if _engine else 0,
        'tests': []
    }
    
    # Test 1: Simple query
    start = time.time()
    try:
        with get_db_session() as session:
            session.execute(text("SELECT 1"))
        results['tests'].append({
            'name': 'simple_query',
            'success': True,
            'time_ms': int((time.time() - start) * 1000)
        })
    except Exception as e:
        results['tests'].append({
            'name': 'simple_query',
            'success': False,
            'error': str(e)
        })
    
    # Test 2: Dashboard metrics
    start = time.time()
    try:
        metrics = get_dashboard_metrics()
        results['tests'].append({
            'name': 'dashboard_metrics',
            'success': True,
            'time_ms': int(metrics.get('query_time_ms', 0)),
            'farmers': metrics.get('total_farmers', 0)
        })
    except Exception as e:
        results['tests'].append({
            'name': 'dashboard_metrics',
            'success': False,
            'error': str(e)
        })
    
    return results

# Initialize pool on module import
if os.getenv('DB_HOST'):
    try:
        init_connection_pool()
    except Exception as e:
        logger.error(f"Failed to initialize connection pool on import: {e}")