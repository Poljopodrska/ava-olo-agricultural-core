# AVA OLO Database Access Guide for Claude Code

## Overview
This guide provides secure, read-only database access for Claude Code development and testing through ECS ALB endpoints.

## Quick Start

### Basic Usage
```python
from ava_database_helper import AVADatabaseAccess

# Initialize database access
db = AVADatabaseAccess()

# Get farmer count
total_farmers = db.count_farmers()
print(f"Total farmers: {total_farmers}")

# Get farmer overview
overview = db.get_farmer_overview()
print(overview)
```

## Available Endpoints

### 1. Database Tables
- **URL**: `GET /dev/db/tables`
- **Purpose**: List all database tables with row and column counts
- **Authentication**: Required

### 2. Database Schema
- **URL**: `GET /dev/db/schema`  
- **Purpose**: Get complete database structure information
- **Authentication**: Required

### 3. Execute Query
- **URL**: `POST /dev/db/query`
- **Purpose**: Execute SELECT queries safely
- **Authentication**: Required
- **Restrictions**: Only SELECT statements allowed

## Authentication

All endpoints require the `X-Dev-Key` header:
```
X-Dev-Key: ava-dev-2025-secure-key
```

## Security Features

### ✅ Query Restrictions
- **SELECT ONLY**: Only SELECT statements are allowed
- **Forbidden Operations**: DELETE, UPDATE, INSERT, DROP, CREATE, ALTER, TRUNCATE blocked
- **Environment Gated**: Only works when `ENVIRONMENT=development`

### ✅ Authentication
- **Required Header**: `X-Dev-Key` must be present
- **Invalid Key**: Returns 401 Unauthorized
- **Missing Key**: Returns 401 Unauthorized

### ✅ Audit Logging
- **All Queries Logged**: Every query execution is logged for security audit
- **Timestamp Tracking**: All access attempts are timestamped
- **Error Tracking**: Failed attempts and errors are logged

## Helper Class Methods

### Basic Access
```python
db = AVADatabaseAccess()

# Test connection
tables = db.get_tables()
if tables.get('success'):
    print(f"Connected! Found {tables['count']} tables")

# Get database schema
schema = db.get_schema()
print(f"Tables: {schema['tables']}")

# Execute custom query
result = db.query("SELECT COUNT(*) as total FROM ava_farmers")
print(f"Result: {result['rows']}")
```

### Farmer Analytics
```python
# Get farmer statistics
overview = db.get_farmer_overview()
print(f"Total farmers: {overview['rows'][0]['total_farmers']}")
print(f"Total hectares: {overview['rows'][0]['total_hectares']}")

# Get recent registrations
recent = db.get_recent_registrations(limit=5)
for farmer in recent['rows']:
    print(f"- {farmer['manager_name']} {farmer['manager_last_name']} ({farmer['farm_name']})")

# Search farmers
results = db.search_farmers("Marko")
for farmer in results['rows']:
    print(f"Found: {farmer['manager_name']} {farmer['manager_last_name']}")
```

### Agricultural Data
```python
# Get crop distribution
crops = db.get_crop_distribution()
for crop in crops['rows']:
    print(f"{crop['crop_name']}: {crop['total_hectares']} hectares in {crop['field_count']} fields")

# Get conversation topics
topics = db.get_conversation_topics()
for topic in topics['rows']:
    print(f"Topic '{topic['topic']}': {topic['conversation_count']} conversations")
```

### Table Analysis
```python
# Get detailed table information
table_info = db.get_table_info("ava_farmers")
print(f"Table: {table_info['table_name']}")
print(f"Columns: {len(table_info['structure']['columns'])}")
print(f"Sample data: {len(table_info['sample_data'])} rows")
```

## Available Database Tables

Based on the current database schema:

### Core Tables
- **ava_farmers**: Farmer profiles and registration data
- **ava_fields**: Field boundaries and information  
- **ava_field_crops**: Crop plantings and status
- **ava_conversations**: Chat history and support requests
- **farm_tasks**: Agricultural tasks and activities

### Support Tables
- **conversation_state**: Chat state management
- **cp_products**: Crop protection products
- **system_health_log**: System monitoring

## Common Queries

### Farmer Statistics
```sql
SELECT 
    COUNT(*) as total_farmers,
    COUNT(DISTINCT city) as cities_covered,
    SUM(total_hectares) as total_hectares,
    AVG(total_hectares) as avg_hectares_per_farmer
FROM ava_farmers
```

### Crop Distribution
```sql
SELECT 
    fc.crop_name,
    COUNT(*) as field_count,
    SUM(f.field_size) as total_hectares
FROM ava_field_crops fc
JOIN ava_fields f ON fc.field_id = f.field_id
WHERE fc.status = 'active'
GROUP BY fc.crop_name
ORDER BY total_hectares DESC
```

### Recent Activity
```sql
SELECT 
    COUNT(*) as recent_conversations
FROM ava_conversations 
WHERE created_at > NOW() - INTERVAL '7 days'
```

### Farmer Fields
```sql
SELECT 
    f.manager_name,
    f.manager_last_name,
    COUNT(fi.field_id) as field_count,
    SUM(fi.field_size) as total_field_size
FROM ava_farmers f
LEFT JOIN ava_fields fi ON f.id = fi.farmer_id
GROUP BY f.id, f.manager_name, f.manager_last_name
ORDER BY total_field_size DESC
```

## Error Handling

### Common Errors
```python
result = db.query("SELECT * FROM ava_farmers LIMIT 5")

if result.get('success'):
    print("Query successful!")
    for row in result['rows']:
        print(row)
else:
    print(f"Error: {result.get('error')}")
```

### Error Types
- **401 Unauthorized**: Missing or invalid `X-Dev-Key`
- **400 Bad Request**: Non-SELECT query attempted
- **403 Forbidden**: Not in development environment
- **500 Internal Server Error**: Database connection or query error

## Configuration

### Environment Variables
```bash
ENVIRONMENT=development          # Required for endpoints to work
DEV_ACCESS_KEY=ava-dev-2025-secure-key    # Authentication key
```

### Base URL
```python
# Default (ECS ALB)
db = AVADatabaseAccess()

# Custom URL
db = AVADatabaseAccess(base_url="http://custom-endpoint.com")

# Custom key
db = AVADatabaseAccess(dev_key="custom-key")
```

## Troubleshooting

### Connection Issues
```python
# Test basic connectivity
import requests
response = requests.get("http://ava-olo-alb-65365776.us-east-1.elb.amazonaws.com/health")
print(f"Health check: {response.status_code}")
```

### Authentication Issues
```python
# Test authentication
headers = {"X-Dev-Key": "ava-dev-2025-secure-key"}
response = requests.get(
    "http://ava-olo-alb-65365776.us-east-1.elb.amazonaws.com/dev/db/tables",
    headers=headers
)
print(f"Auth test: {response.status_code}")
```

### Debug Mode
```python
# Enable detailed output
from ava_database_helper import print_query_results

result = db.get_farmer_overview()
print_query_results(result, "Farmer Overview Debug")
```

## Production Safety

### Development Only
- Endpoints only work when `ENVIRONMENT=development`
- Automatically disabled in production deployments
- No risk to production data integrity

### Read-Only Access
- Only SELECT queries permitted
- No data modification possible
- Database structure cannot be altered

### Monitoring
- All queries logged for audit
- Rate limiting can be added if needed
- Access patterns monitored

## Example Session

```python
from ava_database_helper import AVADatabaseAccess, print_query_results

# Initialize
db = AVADatabaseAccess()

# Test connection
print("Testing connection...")
tables = db.get_tables()
if tables.get('success'):
    print(f"✅ Connected! Found {tables['count']} tables")
else:
    print(f"❌ Connection failed: {tables.get('error')}")
    exit(1)

# Explore farmers
print_query_results(db.get_farmer_overview(), "Farmer Overview")
print_query_results(db.get_recent_registrations(3), "Recent Registrations")
print_query_results(db.get_crop_distribution(), "Crop Distribution")

# Custom analysis
custom_query = """
SELECT 
    city,
    COUNT(*) as farmers,
    SUM(total_hectares) as hectares
FROM ava_farmers 
WHERE city IS NOT NULL 
GROUP BY city 
ORDER BY farmers DESC 
LIMIT 5
"""
print_query_results(db.query(custom_query), "Top Cities by Farmer Count")

print("✅ Database exploration complete!")
```

This guide provides secure, comprehensive access to the AVA OLO farmer database for development and analysis purposes.