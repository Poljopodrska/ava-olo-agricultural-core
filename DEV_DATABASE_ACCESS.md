# Development Database Access Guide

This guide explains how to use the development database endpoints for Claude Code access to the AVA OLO database.

## Quick Start

### 1. Python Helper (Recommended)
```python
from dev_db_helper import DevDatabaseHelper

# Initialize helper
db = DevDatabaseHelper()

# List all tables
tables = db.list_tables()
print(f"Found {tables['count']} tables")

# Get database schema
schema = db.get_schema()
print(f"Tables: {', '.join(schema['tables'])}")

# Run a query
result = db.query("SELECT COUNT(*) as farmer_count FROM ava_farmers")
print(f"Farmers: {result['rows'][0]['farmer_count']}")
```

### 2. Direct HTTP Requests
```python
import requests
from ecs_config import get_dev_db_url

base_url = get_dev_db_url()  # ECS-first with App Runner fallback
headers = {"X-Dev-Key": "temporary-dev-key-2025"}

# List tables
response = requests.get(f"{base_url}/dev/db/tables", headers=headers)
print(response.json())

# Execute query
query_data = {"query": "SELECT COUNT(*) as total FROM ava_farmers"}
response = requests.post(f"{base_url}/dev/db/query", headers=headers, json=query_data)
print(response.json())
```

## Available Endpoints

### 1. List Tables
- **URL**: `GET /dev/db/tables`
- **Purpose**: Get overview of all database tables
- **Returns**: Table names, column counts, row counts

```python
db = DevDatabaseHelper()
tables = db.list_tables()
```

### 2. Database Schema
- **URL**: `GET /dev/db/schema`
- **Purpose**: Get complete database schema information
- **Returns**: Detailed column information for all tables

```python
schema = db.get_schema()
print(schema['schema']['ava_farmers']['columns'])
```

### 3. Execute Query
- **URL**: `POST /dev/db/query`
- **Purpose**: Execute SELECT queries safely
- **Restrictions**: Only SELECT statements allowed

```python
result = db.query("SELECT * FROM ava_farmers LIMIT 5")
for row in result['rows']:
    print(row)
```

## Common Queries

### Farmer Overview
```sql
SELECT 
    COUNT(*) as total_farmers,
    COUNT(DISTINCT city) as cities,
    SUM(total_hectares) as total_hectares,
    AVG(total_hectares) as avg_hectares_per_farmer
FROM ava_farmers
```

### Recent Activity
```sql
SELECT COUNT(*) as recent_conversations 
FROM ava_conversations 
WHERE created_at > NOW() - INTERVAL '7 days'
```

### Field Distribution
```sql
SELECT 
    crop_name,
    COUNT(*) as field_count,
    SUM(fc.field_size) as total_hectares
FROM ava_field_crops fc
JOIN ava_fields f ON fc.field_id = f.field_id
WHERE fc.status = 'active'
GROUP BY crop_name
ORDER BY total_hectares DESC
```

### Conversation Topics
```sql
SELECT 
    topic,
    COUNT(*) as conversation_count
FROM ava_conversations 
WHERE topic IS NOT NULL
GROUP BY topic
ORDER BY conversation_count DESC
LIMIT 10
```

## Security Features

### ✅ Authentication
- Requires `X-Dev-Key` header
- Key: `temporary-dev-key-2025`
- Unauthorized requests return 401

### ✅ Query Restrictions
- Only SELECT statements allowed
- Forbidden operations blocked:
  - DELETE, UPDATE, INSERT
  - DROP, CREATE, ALTER
  - TRUNCATE, GRANT, REVOKE

### ✅ Environment Protection
- Only works when `ENVIRONMENT=development`
- Production deployments automatically disable endpoints

### ✅ Audit Logging
- All queries logged for security audit
- Timestamp and query content recorded

## Helper Functions

The `DevDatabaseHelper` class provides convenient methods:

```python
db = DevDatabaseHelper()

# Table operations
db.describe_table("ava_farmers")
db.count_rows("ava_farmers")
db.sample_data("ava_farmers", limit=3)

# Analysis shortcuts
db.farmers_overview()
db.recent_activity(hours=24)

# Custom queries
db.query("SELECT * FROM ava_conversations ORDER BY created_at DESC LIMIT 5")
```

## Example Session

```python
from dev_db_helper import DevDatabaseHelper, print_results

# Initialize
db = DevDatabaseHelper()

# Explore database
tables = db.list_tables()
print(f"Database has {tables['count']} tables")

# Look at farmers
farmers = db.describe_table("ava_farmers")
print(f"Farmers table has {farmers['details']['column_count']} columns")

# Get sample data
sample = db.sample_data("ava_farmers", limit=3)
print_results(sample)

# Analyze activity
activity = db.recent_activity(hours=24)
print_results(activity)
```

## Troubleshooting

### 404 Not Found
- Check that endpoints are deployed to App Runner
- Verify the base URL is correct
- Ensure `ENVIRONMENT=development` is set

### 401 Unauthorized
- Check `X-Dev-Key` header is set correctly
- Verify key value: `temporary-dev-key-2025`

### 403 Forbidden
- Endpoints only work in development environment
- Check `ENVIRONMENT` variable is set to `development`

### 400 Bad Request
- Only SELECT queries are allowed
- Remove forbidden keywords (DELETE, UPDATE, etc.)
- Check query syntax

## Deployment Requirements

To enable these endpoints in production:

1. Set environment variables:
   ```
   ENVIRONMENT=development
   DEV_ACCESS_KEY=temporary-dev-key-2025
   ```

2. Deploy monitoring service with updated code

3. Test endpoints are available

4. **Important**: Remove before production deployment

## Security Warning

⚠️ **These endpoints are for development only**

- Remove before production deployment
- Do not use in production environment
- Change the access key in real deployments
- Monitor access logs for unauthorized usage

The endpoints automatically disable when `ENVIRONMENT != development` for safety.