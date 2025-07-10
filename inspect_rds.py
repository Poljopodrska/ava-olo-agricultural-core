"""
RDS Database Structure Inspector
Inspects PostgreSQL database schemas and tables structure
Can be deployed to AWS App Runner as part of the database explorer
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
from datetime import datetime

# Import database configuration
from config import DATABASE_URL, DB_POOL_SETTINGS

logger = logging.getLogger(__name__)

class RDSInspector:
    """Inspector for RDS PostgreSQL database structure"""
    
    def __init__(self, connection_string: str = None):
        """Initialize with database connection"""
        self.connection_string = connection_string or DATABASE_URL
        
        # Create engine with connection pooling
        self.engine = create_engine(
            self.connection_string,
            **DB_POOL_SETTINGS
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def inspect_database_structure(self) -> Dict[str, Any]:
        """
        Inspect complete database structure including:
        - All schemas
        - All tables in each schema
        - Table columns and types
        - Row counts
        - Tables outside public schema
        """
        try:
            with self.get_session() as session:
                inspector = inspect(session.bind)
                
                # Get all schemas
                schemas_result = session.execute(
                    text("""
                        SELECT schema_name 
                        FROM information_schema.schemata 
                        WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                        ORDER BY schema_name
                    """)
                ).fetchall()
                
                schemas = [row[0] for row in schemas_result]
                
                # Structure to hold all information
                database_structure = {
                    "inspection_timestamp": datetime.now().isoformat(),
                    "database_name": self.connection_string.split('/')[-1].split('?')[0],
                    "total_schemas": len(schemas),
                    "schemas": {},
                    "tables_outside_public": [],
                    "summary": {
                        "total_tables": 0,
                        "total_rows": 0,
                        "schemas_with_tables": 0
                    }
                }
                
                # Inspect each schema
                for schema_name in schemas:
                    schema_info = {
                        "tables": {},
                        "table_count": 0,
                        "total_rows": 0
                    }
                    
                    # Get tables in this schema
                    tables_result = session.execute(
                        text("""
                            SELECT table_name 
                            FROM information_schema.tables 
                            WHERE table_schema = :schema_name 
                            AND table_type = 'BASE TABLE'
                            ORDER BY table_name
                        """),
                        {"schema_name": schema_name}
                    ).fetchall()
                    
                    tables = [row[0] for row in tables_result]
                    schema_info["table_count"] = len(tables)
                    
                    if len(tables) > 0:
                        database_structure["summary"]["schemas_with_tables"] += 1
                    
                    # Inspect each table
                    for table_name in tables:
                        table_info = self._inspect_table(session, schema_name, table_name)
                        schema_info["tables"][table_name] = table_info
                        schema_info["total_rows"] += table_info.get("row_count", 0)
                        
                        # Track tables outside public schema
                        if schema_name != 'public':
                            database_structure["tables_outside_public"].append({
                                "schema": schema_name,
                                "table": table_name,
                                "row_count": table_info.get("row_count", 0)
                            })
                    
                    database_structure["schemas"][schema_name] = schema_info
                    database_structure["summary"]["total_tables"] += schema_info["table_count"]
                    database_structure["summary"]["total_rows"] += schema_info["total_rows"]
                
                # Add specific checks for non-public schemas
                database_structure["non_public_analysis"] = self._analyze_non_public_schemas(database_structure)
                
                return database_structure
                
        except Exception as e:
            logger.error(f"Error inspecting database structure: {str(e)}")
            return {
                "error": str(e),
                "inspection_timestamp": datetime.now().isoformat()
            }
    
    def _inspect_table(self, session, schema_name: str, table_name: str) -> Dict[str, Any]:
        """Inspect individual table structure and data"""
        try:
            # Get columns
            columns_result = session.execute(
                text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_schema = :schema_name AND table_name = :table_name
                    ORDER BY ordinal_position
                """),
                {"schema_name": schema_name, "table_name": table_name}
            ).fetchall()
            
            columns = []
            for col in columns_result:
                columns.append({
                    "name": col[0],
                    "type": col[1],
                    "nullable": col[2] == 'YES',
                    "default": col[3]
                })
            
            # Get row count
            try:
                if schema_name == 'public':
                    count_query = f"SELECT COUNT(*) FROM {table_name}"
                else:
                    count_query = f"SELECT COUNT(*) FROM {schema_name}.{table_name}"
                    
                row_count = session.execute(text(count_query)).scalar() or 0
            except:
                row_count = 0
            
            # Get primary keys
            pk_result = session.execute(
                text("""
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                    AND tc.table_schema = :schema_name
                    AND tc.table_name = :table_name
                """),
                {"schema_name": schema_name, "table_name": table_name}
            ).fetchall()
            
            primary_keys = [row[0] for row in pk_result]
            
            # Get foreign keys
            fk_result = session.execute(
                text("""
                    SELECT 
                        kcu.column_name,
                        ccu.table_schema AS foreign_table_schema,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                        AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = :schema_name
                    AND tc.table_name = :table_name
                """),
                {"schema_name": schema_name, "table_name": table_name}
            ).fetchall()
            
            foreign_keys = []
            for fk in fk_result:
                foreign_keys.append({
                    "column": fk[0],
                    "references": f"{fk[1]}.{fk[2]}.{fk[3]}"
                })
            
            # Get indexes
            index_result = session.execute(
                text("""
                    SELECT indexname, indexdef
                    FROM pg_indexes
                    WHERE schemaname = :schema_name
                    AND tablename = :table_name
                """),
                {"schema_name": schema_name, "table_name": table_name}
            ).fetchall()
            
            indexes = [{"name": idx[0], "definition": idx[1]} for idx in index_result]
            
            return {
                "row_count": row_count,
                "column_count": len(columns),
                "columns": columns,
                "primary_keys": primary_keys,
                "foreign_keys": foreign_keys,
                "indexes": indexes,
                "has_data": row_count > 0
            }
            
        except Exception as e:
            logger.error(f"Error inspecting table {schema_name}.{table_name}: {str(e)}")
            return {
                "error": str(e),
                "row_count": 0,
                "column_count": 0
            }
    
    def _analyze_non_public_schemas(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze tables outside public schema"""
        analysis = {
            "has_non_public_tables": len(structure["tables_outside_public"]) > 0,
            "non_public_table_count": len(structure["tables_outside_public"]),
            "non_public_row_count": sum(t["row_count"] for t in structure["tables_outside_public"]),
            "schemas_with_data": []
        }
        
        for schema_name, schema_info in structure["schemas"].items():
            if schema_name != 'public' and schema_info["total_rows"] > 0:
                analysis["schemas_with_data"].append({
                    "schema": schema_name,
                    "table_count": schema_info["table_count"],
                    "row_count": schema_info["total_rows"]
                })
        
        return analysis
    
    def get_schema_list(self) -> List[str]:
        """Get list of all schemas (excluding system schemas)"""
        try:
            with self.get_session() as session:
                result = session.execute(
                    text("""
                        SELECT schema_name 
                        FROM information_schema.schemata 
                        WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                        ORDER BY schema_name
                    """)
                ).fetchall()
                
                return [row[0] for row in result]
                
        except Exception as e:
            logger.error(f"Error getting schema list: {str(e)}")
            return []
    
    def get_table_list(self, schema_name: str = 'public') -> List[Dict[str, Any]]:
        """Get list of tables in a specific schema"""
        try:
            with self.get_session() as session:
                result = session.execute(
                    text("""
                        SELECT 
                            t.table_name,
                            pg_size_pretty(pg_total_relation_size(quote_ident(t.table_schema)||'.'||quote_ident(t.table_name))) as size,
                            obj_description(c.oid) as comment
                        FROM information_schema.tables t
                        LEFT JOIN pg_class c ON c.relname = t.table_name
                        LEFT JOIN pg_namespace n ON n.oid = c.relnamespace AND n.nspname = t.table_schema
                        WHERE t.table_schema = :schema_name 
                        AND t.table_type = 'BASE TABLE'
                        ORDER BY t.table_name
                    """),
                    {"schema_name": schema_name}
                ).fetchall()
                
                tables = []
                for row in result:
                    tables.append({
                        "name": row[0],
                        "size": row[1],
                        "comment": row[2] or ""
                    })
                
                return tables
                
        except Exception as e:
            logger.error(f"Error getting table list for schema {schema_name}: {str(e)}")
            return []


# FastAPI integration functions
def create_inspect_endpoint(app, db_ops):
    """Add RDS inspection endpoint to existing FastAPI app"""
    
    inspector = RDSInspector(db_ops.connection_string)
    
    @app.get("/api/inspect/database")
    async def inspect_database():
        """Inspect complete database structure"""
        try:
            structure = inspector.inspect_database_structure()
            return {
                "success": True,
                "data": structure
            }
        except Exception as e:
            logger.error(f"Database inspection failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/inspect/schemas")
    async def list_schemas():
        """List all database schemas"""
        try:
            schemas = inspector.get_schema_list()
            return {
                "success": True,
                "schemas": schemas,
                "count": len(schemas)
            }
        except Exception as e:
            logger.error(f"Schema listing failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/inspect/tables/{schema_name}")
    async def list_schema_tables(schema_name: str):
        """List all tables in a specific schema"""
        try:
            tables = inspector.get_table_list(schema_name)
            return {
                "success": True,
                "schema": schema_name,
                "tables": tables,
                "count": len(tables)
            }
        except Exception as e:
            logger.error(f"Table listing failed for schema {schema_name}: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return inspector


# Standalone execution for testing
if __name__ == "__main__":
    import sys
    
    print("🔍 RDS Database Structure Inspector")
    print("=" * 50)
    
    # Initialize inspector
    inspector = RDSInspector()
    
    # Run inspection
    print("\n📊 Inspecting database structure...")
    structure = inspector.inspect_database_structure()
    
    if "error" in structure:
        print(f"\n❌ Inspection failed: {structure['error']}")
        sys.exit(1)
    
    # Print results
    print(f"\n✅ Inspection completed at: {structure['inspection_timestamp']}")
    print(f"\n📋 Database: {structure['database_name']}")
    print(f"   Total schemas: {structure['total_schemas']}")
    print(f"   Total tables: {structure['summary']['total_tables']}")
    print(f"   Total rows: {structure['summary']['total_rows']:,}")
    
    print("\n📁 Schemas:")
    for schema_name, schema_info in structure['schemas'].items():
        print(f"\n   {schema_name}:")
        print(f"     Tables: {schema_info['table_count']}")
        print(f"     Total rows: {schema_info['total_rows']:,}")
        
        if schema_info['table_count'] > 0:
            print("     Tables:")
            for table_name, table_info in schema_info['tables'].items():
                print(f"       - {table_name}: {table_info['row_count']:,} rows, {table_info['column_count']} columns")
    
    if structure['tables_outside_public']:
        print(f"\n⚠️  Found {len(structure['tables_outside_public'])} tables outside 'public' schema:")
        for table in structure['tables_outside_public']:
            print(f"   - {table['schema']}.{table['table']}: {table['row_count']:,} rows")
    else:
        print("\n✅ All tables are in the 'public' schema")
    
    # Save results to JSON file
    output_file = f"rds_inspection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(structure, f, indent=2, default=str)
    
    print(f"\n💾 Full inspection results saved to: {output_file}")