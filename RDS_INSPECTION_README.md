# RDS Database Inspection Tools

This directory contains tools for inspecting the RDS PostgreSQL database structure, particularly useful for understanding schema organization and identifying tables outside the 'public' schema.

## Files Created

### 1. `inspect_rds.py`
Main inspection module that can be integrated into the existing database explorer. Provides comprehensive database structure analysis.

**Features:**
- Lists all database schemas
- Enumerates tables in each schema
- Provides detailed table information (columns, types, constraints)
- Counts rows in each table
- Identifies tables outside the 'public' schema
- Analyzes foreign keys and indexes

**Integration:**
Already integrated into `database_explorer.py` with the following endpoints:
- `/api/inspect/database` - Full database structure inspection
- `/api/inspect/schemas` - List all schemas
- `/api/inspect/tables/{schema_name}` - List tables in a specific schema

### 2. `inspect_rds_standalone.py`
Standalone script using psycopg2 for direct database inspection. Can be run independently without the full application stack.

**Usage:**
```bash
python3 inspect_rds_standalone.py
# Or save results to file:
python3 inspect_rds_standalone.py --save
```

### 3. `inspect_rds_api.py`
Lightweight FastAPI service specifically for RDS inspection. Ideal for AWS App Runner deployment.

**Endpoints:**
- `/` - Service information
- `/health` - Health check
- `/inspect` - Full database inspection
- `/schemas` - List all schemas
- `/tables/{schema_name}` - List tables in a schema

**Deployment:**
```bash
# Run locally
python3 inspect_rds_api.py

# The service will start on port 8006 (or PORT env variable)
```

## Environment Variables Required

All inspection tools use the same environment variables:
```
DB_HOST=your-rds-endpoint.amazonaws.com
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password
```

## AWS App Runner Deployment

For AWS App Runner deployment, use `inspect_rds_api.py`:

1. Create a Dockerfile:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY inspect_rds_api.py .
COPY config.py .

EXPOSE 8006

CMD ["python", "inspect_rds_api.py"]
```

2. Configure App Runner with the required environment variables

3. Access the inspection endpoints through the App Runner URL

## Example Output

The inspection returns JSON with the following structure:
```json
{
  "inspection_timestamp": "2024-01-09T10:30:00",
  "database_name": "ava_olo",
  "schemas": {
    "public": {
      "table_count": 15,
      "total_rows": 50000,
      "tables": {
        "farmers": {
          "column_count": 10,
          "row_count": 1500
        }
      }
    }
  },
  "tables_outside_public": [
    {
      "schema": "analytics",
      "table": "user_metrics",
      "row_count": 10000
    }
  ],
  "summary": {
    "total_schemas": 3,
    "total_tables": 20,
    "total_rows": 75000
  }
}
```

## Use Cases

1. **Database Migration Planning**: Understand the complete database structure before migration
2. **Schema Analysis**: Identify tables that might need to be moved to the public schema
3. **Database Documentation**: Generate comprehensive database structure documentation
4. **Monitoring**: Track database growth and table distribution across schemas
5. **Troubleshooting**: Quickly identify where data is stored across different schemas