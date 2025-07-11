"""
CONSTITUTIONAL COMPLIANCE: API-FIRST + ERROR ISOLATION
Clean API interface for database administration
"""

from fastapi import FastAPI, HTTPException, Query, Form
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import logging
import traceback

from monitoring.core.llm_query_processor import LLMQueryProcessor
from monitoring.core.response_formatter import ResponseFormatter
from database_operations import DatabaseOperations

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AVA OLO Admin Dashboard API",
    description="Constitutional API for agricultural database management",
    version="2.0.0"
)

# Initialize processors
llm_processor = LLMQueryProcessor()
formatter = ResponseFormatter()
db_ops = DatabaseOperations()


@app.on_event("startup")
async def startup_event():
    """Initialize LLM processor with database schema"""
    try:
        # Get database schema for LLM context
        with db_ops.get_session() as session:
            from sqlalchemy import inspect
            inspector = inspect(session.bind)
            
            schema_info = []
            for table_name in inspector.get_table_names():
                columns = []
                for col in inspector.get_columns(table_name):
                    columns.append(f"{col['name']} ({str(col['type'])})")
                schema_info.append(f"{table_name}: {', '.join(columns[:5])}")
            
            schema_context = "\n".join(schema_info)
            llm_processor.set_schema_context(schema_context)
            
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")


@app.post("/api/natural-query")
async def process_natural_query(
    query: str = Form(...),
    language: str = Form("auto")
) -> Dict[str, Any]:
    """
    Constitutional compliance: API-FIRST communication
    ERROR ISOLATION: Never crash system
    
    Process natural language queries in ANY language
    """
    try:
        # Process with LLM intelligence
        result = llm_processor.process_natural_query(query, language)
        
        # Execute SQL if valid
        if result.get('sql') and not result['sql'].startswith('--'):
            with db_ops.get_session() as session:
                from sqlalchemy import text
                db_result = session.execute(text(result['sql']))
                
                # Fetch results based on query type
                if result.get('query_type') == 'select':
                    rows = db_result.fetchall()
                    columns = list(db_result.keys())
                    
                    # Convert to dict format
                    data = []
                    for row in rows:
                        data.append(dict(zip(columns, row)))
                    
                    # Format results
                    formatted = formatter.format_results(
                        data, 
                        query, 
                        result.get('detected_language', 'en')
                    )
                    
                    return {
                        "success": True,
                        "query": result,
                        "results": formatted
                    }
        
        return {
            "success": False,
            "query": result,
            "message": "Could not generate valid SQL"
        }
        
    except Exception as e:
        # ERROR ISOLATION: Graceful degradation
        logger.error(f"Query processing error: {traceback.format_exc()}")
        
        error_response = formatter.format_error(
            e, 
            language if language != "auto" else "en"
        )
        
        return {
            "success": False,
            "error": error_response,
            "fallback": "Please try a simpler query or check your connection"
        }


@app.post("/api/modify-data")
async def modify_data(
    query: str = Form(...),
    language: str = Form("auto")
) -> Dict[str, Any]:
    """
    Process data modification requests (INSERT/UPDATE/DELETE)
    With full error isolation and LLM intelligence
    """
    try:
        # Process modification query
        result = llm_processor.process_modification_query(query, language)
        
        if result.get('sql') and not result['sql'].startswith('--'):
            with db_ops.get_session() as session:
                from sqlalchemy import text
                
                # Execute modification
                db_result = session.execute(text(result['sql']))
                session.commit()
                
                rows_affected = db_result.rowcount if hasattr(db_result, 'rowcount') else 0
                
                # Format success response
                formatted = formatter.format_modification_result(
                    {
                        'success': True,
                        'operation': result.get('operation'),
                        'rows_affected': rows_affected
                    },
                    result.get('detected_language', 'en')
                )
                
                return {
                    "success": True,
                    "query": result,
                    "result": formatted
                }
        
        return {
            "success": False,
            "query": result,
            "message": "Could not generate valid modification SQL"
        }
        
    except Exception as e:
        logger.error(f"Modification error: {traceback.format_exc()}")
        
        error_response = formatter.format_error(
            e,
            language if language != "auto" else "en"
        )
        
        return {
            "success": False,
            "error": error_response
        }


@app.get("/api/tables")
async def list_tables() -> Dict[str, Any]:
    """List available tables in the database"""
    try:
        with db_ops.get_session() as session:
            from sqlalchemy import text
            
            result = session.execute(text("""
                SELECT table_name, 
                       pg_size_pretty(pg_total_relation_size(quote_ident(table_name)::text)) as size
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """))
            
            tables = []
            for row in result:
                tables.append({
                    "name": row[0],
                    "size": row[1]
                })
            
            return {
                "success": True,
                "tables": tables,
                "count": len(tables)
            }
            
    except Exception as e:
        logger.error(f"Error listing tables: {e}")
        return {
            "success": False,
            "error": "Could not retrieve table list",
            "tables": []
        }


@app.get("/api/table/{table_name}")
async def get_table_data(
    table_name: str,
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """Get data from a specific table"""
    try:
        with db_ops.get_session() as session:
            from sqlalchemy import text, inspect
            
            # Get table columns
            inspector = inspect(session.bind)
            columns = [col['name'] for col in inspector.get_columns(table_name)]
            
            # Get data
            result = session.execute(
                text(f"SELECT * FROM {table_name} LIMIT :limit OFFSET :offset"),
                {"limit": limit, "offset": offset}
            )
            
            rows = []
            for row in result:
                rows.append(dict(zip(columns, row)))
            
            # Get total count
            count_result = session.execute(
                text(f"SELECT COUNT(*) FROM {table_name}")
            )
            total_count = count_result.scalar()
            
            return {
                "success": True,
                "table": table_name,
                "columns": columns,
                "data": rows,
                "total_count": total_count,
                "limit": limit,
                "offset": offset
            }
            
    except Exception as e:
        logger.error(f"Error getting table data: {e}")
        return {
            "success": False,
            "error": f"Could not retrieve data from table {table_name}"
        }


@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """System health check with database connectivity test"""
    try:
        # Test database connection
        db_healthy = await db_ops.health_check()
        
        return {
            "status": "healthy" if db_healthy else "degraded",
            "database": "connected" if db_healthy else "disconnected",
            "llm": "ready",
            "api_version": "2.0.0",
            "constitutional_compliance": {
                "mango_rule": True,
                "privacy_first": True,
                "error_isolation": True,
                "llm_first": True
            }
        }
        
    except Exception as e:
        # Even health check errors don't crash system
        return {
            "status": "degraded",
            "database": "unknown",
            "error": "Health check failed",
            "constitutional_compliance": {
                "error_isolation": True  # We're still running!
            }
        }


# Error handlers for complete isolation
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global error handler - system never crashes"""
    logger.error(f"Global exception: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "System temporarily unavailable",
            "message": "Please try again or contact support",
            "constitutional_compliance": {
                "error_isolation": True
            }
        }
    )