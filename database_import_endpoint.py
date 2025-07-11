"""
Add this to database_explorer.py to import database via API
"""
from fastapi import File, UploadFile
import tempfile

@app.post("/api/import-database")
async def import_database(sql_file: UploadFile = File(...)):
    """Import database structure from SQL file"""
    try:
        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.sql') as tmp:
            content = await sql_file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Read and parse SQL
        with open(tmp_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Split into statements (basic splitting by semicolon)
        statements = []
        current = []
        in_function = False
        
        for line in sql_content.split('\n'):
            # Skip comments
            if line.strip().startswith('--'):
                continue
                
            # Track if we're inside a function/procedure
            if 'CREATE FUNCTION' in line or 'CREATE PROCEDURE' in line:
                in_function = True
            if in_function and line.strip() == '$$ LANGUAGE':
                in_function = False
                
            current.append(line)
            
            # End of statement
            if not in_function and line.strip().endswith(';'):
                statement = '\n'.join(current).strip()
                if statement and not statement.startswith('--'):
                    statements.append(statement)
                current = []
        
        # Execute statements
        executed = 0
        errors = []
        tables_created = []
        
        with db_ops.get_session() as session:
            for i, statement in enumerate(statements):
                try:
                    # Extract table name if it's a CREATE TABLE
                    if 'CREATE TABLE' in statement:
                        table_match = re.search(r'CREATE TABLE\s+(?:IF NOT EXISTS\s+)?["]?(\w+)[.]?["]?(\w+)?', statement)
                        if table_match:
                            table_name = table_match.group(2) if table_match.group(2) else table_match.group(1)
                            tables_created.append(table_name)
                    
                    session.execute(text(statement))
                    session.commit()
                    executed += 1
                    
                except Exception as e:
                    error_msg = str(e)
                    # Skip some common non-critical errors
                    if 'already exists' in error_msg or 'does not exist' in error_msg:
                        session.rollback()
                        continue
                    errors.append(f"Statement {i+1}: {error_msg[:100]}")
                    session.rollback()
        
        # Clean up
        os.unlink(tmp_path)
        
        return {
            "success": len(errors) == 0,
            "total_statements": len(statements),
            "executed": executed,
            "tables_created": tables_created,
            "errors": errors[:10]  # First 10 errors
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }