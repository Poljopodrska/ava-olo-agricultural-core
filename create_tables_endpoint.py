"""
Add this endpoint to database_explorer.py to create tables via API
"""

@app.post("/api/create-tables")
async def create_tables(request: Request):
    """Create database tables from SQL schema"""
    try:
        # Read the SQL file
        sql_file = "farmer_crm_tables_simple_20250710_194506.sql"
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        # Split into individual CREATE TABLE statements
        statements = []
        current = []
        for line in sql_content.split('\n'):
            if line.strip().startswith('--'):
                continue
            if line.strip():
                current.append(line)
            if line.strip().endswith(';'):
                if current:
                    statements.append('\n'.join(current))
                    current = []
        
        # Execute each statement
        created_tables = []
        errors = []
        
        with db_ops.get_session() as session:
            for statement in statements:
                if 'CREATE TABLE' in statement:
                    try:
                        session.execute(text(statement))
                        session.commit()
                        # Extract table name
                        table_name = statement.split('CREATE TABLE')[1].split('(')[0].strip()
                        created_tables.append(table_name)
                    except Exception as e:
                        errors.append(f"{statement[:50]}... - {str(e)}")
                        session.rollback()
        
        return {
            "success": len(errors) == 0,
            "created_tables": created_tables,
            "errors": errors,
            "total_tables": len(created_tables)
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }