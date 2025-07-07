"""
AVA OLO Database Explorer - Port 8005
User-friendly interface for database exploration and data export
"""
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
import logging
import os
import sys
from typing import Dict, Any, List, Optional
import tempfile
import pandas as pd

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_operations import DatabaseOperations

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AVA OLO Database Explorer",
    description="User-friendly database exploration and data export",
    version="2.0.0"
)

# Setup templates
templates = Jinja2Templates(directory="services/templates")

# Initialize database
db_ops = DatabaseOperations()

class DatabaseExplorer:
    """Database explorer for table browsing and data export"""
    
    def __init__(self):
        self.db_ops = DatabaseOperations()
    
    async def get_tables_info(self) -> List[Dict[str, Any]]:
        """Get information about all tables"""
        try:
            with self.db_ops.get_session() as session:
                from sqlalchemy import text, inspect
                
                inspector = inspect(session.bind)
                tables = []
                
                for table_name in inspector.get_table_names():
                    try:
                        # Get row count
                        row_count = session.execute(
                            text(f"SELECT COUNT(*) FROM {table_name}")
                        ).scalar()
                        
                        # Get column info
                        columns = inspector.get_columns(table_name)
                        
                        tables.append({
                            "name": table_name,
                            "row_count": row_count,
                            "columns": [{"name": col["name"], "type": str(col["type"])} for col in columns],
                            "description": self._get_table_description(table_name)
                        })
                        
                    except Exception as e:
                        logger.warning(f"Error getting info for table {table_name}: {str(e)}")
                        continue
                
                return tables
                
        except Exception as e:
            logger.error(f"Error getting tables info: {str(e)}")
            return []
    
    def _get_table_description(self, table_name: str) -> str:
        """Get human-readable description for table"""
        descriptions = {
            "ava_conversations": "Razgovori između korisnika i AVA sustava",
            "farmers": "Informacije o poljoprivrednicima",
            "fields": "Polja i parcele",
            "crops": "Usjevi i biljke",
            "tasks": "Zadaci i aktivnosti na farmama"
        }
        return descriptions.get(table_name, "")
    
    async def get_table_data(self, table_name: str, page: int = 1, limit: int = 50, 
                           search: str = "", order_by: str = "", order_dir: str = "desc") -> Dict[str, Any]:
        """Get paginated data from a table"""
        try:
            with self.db_ops.get_session() as session:
                from sqlalchemy import text, inspect
                
                inspector = inspect(session.bind)
                columns = [col["name"] for col in inspector.get_columns(table_name)]
                
                # Build query
                query_parts = [f"SELECT * FROM {table_name}"]
                params = {}
                
                # Add search condition
                if search:
                    search_conditions = []
                    for col in columns:
                        search_conditions.append(f"{col}::text ILIKE :search")
                    query_parts.append(f"WHERE ({' OR '.join(search_conditions)})")
                    params["search"] = f"%{search}%"
                
                # Add ordering
                if order_by and order_by in columns:
                    direction = "DESC" if order_dir.lower() == "desc" else "ASC"
                    query_parts.append(f"ORDER BY {order_by} {direction}")
                
                # Get total count
                count_query = query_parts[0].replace("SELECT *", "SELECT COUNT(*)")
                if len(query_parts) > 1 and query_parts[1].startswith("WHERE"):
                    count_query += f" {query_parts[1]}"
                
                total_count = session.execute(text(count_query), params).scalar()
                
                # Add pagination
                offset = (page - 1) * limit
                query_parts.extend([f"LIMIT {limit}", f"OFFSET {offset}"])
                
                # Execute main query
                query = " ".join(query_parts)
                results = session.execute(text(query), params).fetchall()
                
                rows = [list(row) for row in results]
                
                return {
                    "columns": columns,
                    "rows": rows,
                    "total_count": total_count,
                    "page": page,
                    "limit": limit,
                    "has_more": (page * limit) < total_count
                }
                
        except Exception as e:
            logger.error(f"Error getting table data: {str(e)}")
            return {
                "columns": [],
                "rows": [],
                "total_count": 0,
                "page": 1,
                "limit": limit,
                "has_more": False
            }
    
    async def get_column_stats(self, table_name: str) -> List[Dict[str, Any]]:
        """Get statistics for each column in the table"""
        try:
            with self.db_ops.get_session() as session:
                from sqlalchemy import text, inspect
                
                inspector = inspect(session.bind)
                columns = inspector.get_columns(table_name)
                stats = []
                
                for col in columns:
                    col_name = col["name"]
                    col_type = str(col["type"])
                    
                    try:
                        # Basic stats
                        null_count = session.execute(
                            text(f"SELECT COUNT(*) FROM {table_name} WHERE {col_name} IS NULL")
                        ).scalar()
                        
                        unique_count = session.execute(
                            text(f"SELECT COUNT(DISTINCT {col_name}) FROM {table_name}")
                        ).scalar()
                        
                        # Sample values
                        sample_values = session.execute(
                            text(f"SELECT DISTINCT {col_name} FROM {table_name} WHERE {col_name} IS NOT NULL LIMIT 5")
                        ).fetchall()
                        
                        stat_info = {
                            "name": col_name,
                            "type": col_type,
                            "null_count": null_count,
                            "unique_count": unique_count,
                            "sample_values": [str(row[0]) for row in sample_values]
                        }
                        
                        # Additional stats for numeric columns
                        if "int" in col_type.lower() or "float" in col_type.lower() or "numeric" in col_type.lower():
                            try:
                                min_val = session.execute(
                                    text(f"SELECT MIN({col_name}) FROM {table_name}")
                                ).scalar()
                                max_val = session.execute(
                                    text(f"SELECT MAX({col_name}) FROM {table_name}")
                                ).scalar()
                                
                                stat_info["min_value"] = str(min_val) if min_val is not None else None
                                stat_info["max_value"] = str(max_val) if max_val is not None else None
                            except:
                                pass
                        
                        stats.append(stat_info)
                        
                    except Exception as e:
                        logger.warning(f"Error getting stats for column {col_name}: {str(e)}")
                        continue
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting column stats: {str(e)}")
            return []
    
    async def export_table_data(self, table_name: str, format: str = "excel", 
                              search: str = "", limit: int = 10000) -> str:
        """Export table data to file"""
        try:
            # Get data
            data = await self.get_table_data(table_name, page=1, limit=limit, search=search)
            
            if not data["rows"]:
                raise HTTPException(status_code=404, detail="No data to export")
            
            # Create DataFrame
            df = pd.DataFrame(data["rows"], columns=data["columns"])
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{format}") as tmp_file:
                if format.lower() == "excel":
                    df.to_excel(tmp_file.name, index=False)
                elif format.lower() == "csv":
                    df.to_csv(tmp_file.name, index=False)
                else:
                    raise HTTPException(status_code=400, detail="Unsupported format")
                
                return tmp_file.name
                
        except Exception as e:
            logger.error(f"Error exporting data: {str(e)}")
            raise HTTPException(status_code=500, detail="Export failed")

# Initialize explorer
explorer = DatabaseExplorer()

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Database Explorer Dashboard"""
    tables = await explorer.get_tables_info()
    
    return templates.TemplateResponse("database_explorer.html", {
        "request": request,
        "tables": tables
    })

@app.get("/api/schema/tables")
async def get_tables():
    """API endpoint for tables information"""
    return await explorer.get_tables_info()

@app.get("/api/data/{table_name}")
async def get_table_data(
    table_name: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=10, le=1000),
    search: str = Query(""),
    order_by: str = Query(""),
    order_dir: str = Query("desc")
):
    """API endpoint for table data"""
    return await explorer.get_table_data(table_name, page, limit, search, order_by, order_dir)

@app.get("/api/data/{table_name}/columns")
async def get_column_stats(table_name: str):
    """API endpoint for column statistics"""
    return await explorer.get_column_stats(table_name)

@app.get("/api/data/{table_name}/export")
async def export_table(
    table_name: str,
    format: str = Query("excel"),
    search: str = Query(""),
    limit: int = Query(10000)
):
    """Export table data"""
    file_path = await explorer.export_table_data(table_name, format, search, limit)
    
    filename = f"{table_name}.{format}"
    return FileResponse(
        file_path,
        filename=filename,
        media_type="application/octet-stream"
    )

@app.get("/api/query/custom")
async def execute_custom_query(query: str = Query(...), limit: int = Query(1000)):
    """Execute custom SQL query (SELECT only)"""
    try:
        # Security check - only allow SELECT statements
        query_clean = query.strip().upper()
        if not query_clean.startswith("SELECT"):
            raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")
        
        # Prevent dangerous operations
        dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"]
        if any(keyword in query_clean for keyword in dangerous_keywords):
            raise HTTPException(status_code=400, detail="Query contains dangerous operations")
        
        with db_ops.get_session() as session:
            from sqlalchemy import text
            
            # Add limit to query if not present
            if "LIMIT" not in query_clean:
                query += f" LIMIT {limit}"
            
            results = session.execute(text(query)).fetchall()
            
            if results:
                columns = list(results[0].keys())
                rows = [list(row) for row in results]
            else:
                columns = []
                rows = []
            
            return {
                "columns": columns,
                "rows": rows,
                "row_count": len(rows)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing custom query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check"""
    db_healthy = await db_ops.health_check()
    
    return {
        "service": "Database Explorer",
        "status": "healthy",
        "database": "connected" if db_healthy else "disconnected",
        "port": 8005,
        "purpose": "Database exploration and data export"
    }

if __name__ == "__main__":
    import uvicorn
    print("🗃️ Starting AVA OLO Database Explorer on port 8005")
    uvicorn.run(app, host="0.0.0.0", port=8005)