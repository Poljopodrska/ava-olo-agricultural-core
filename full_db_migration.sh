#!/bin/bash
# Full database migration from local to AWS RDS

echo "🚀 Full Database Migration to AWS RDS"
echo "===================================="

# Configuration
LOCAL_DB="farmer_crm"
LOCAL_USER="postgres"
LOCAL_PASS="password"
LOCAL_HOST="localhost"

AWS_HOST="farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com"
AWS_DB="postgres"
AWS_USER="postgres"
AWS_PASS="2hpzvrg_xP~qNbz1[_NppSK\$e*O1"

# Option 1: Full database dump (schema + data)
echo "Creating full database backup..."
PGPASSWORD=$LOCAL_PASS pg_dump -h $LOCAL_HOST -U $LOCAL_USER -d $LOCAL_DB -v -Fc -f farmer_crm_full_backup.dump

# Option 2: Schema only (if you don't need data)
echo "Creating schema-only backup..."
PGPASSWORD=$LOCAL_PASS pg_dump -h $LOCAL_HOST -U $LOCAL_USER -d $LOCAL_DB --schema-only -v -f farmer_crm_schema.sql

# Option 3: Create a SQL file that can be run through Query Editor
echo "Creating SQL script for AWS RDS Query Editor..."
PGPASSWORD=$LOCAL_PASS pg_dump -h $LOCAL_HOST -U $LOCAL_USER -d $LOCAL_DB \
    --schema-only \
    --no-owner \
    --no-privileges \
    --no-tablespaces \
    --no-unlogged-table-data \
    --quote-all-identifiers \
    -f farmer_crm_aws_ready.sql

echo "✅ Backup files created!"
echo ""
echo "📋 Next steps:"
echo "1. For direct restore (requires VPC access):"
echo "   PGPASSWORD='$AWS_PASS' pg_restore -h $AWS_HOST -U $AWS_USER -d $AWS_DB -v farmer_crm_full_backup.dump"
echo ""
echo "2. For AWS RDS Query Editor:"
echo "   - Open farmer_crm_aws_ready.sql"
echo "   - Copy content and paste in Query Editor"
echo ""
echo "3. For partial migration:"
echo "   - Use farmer_crm_schema.sql for structure only"