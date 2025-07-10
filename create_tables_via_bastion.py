#!/usr/bin/env python3
"""
Alternative: Create tables using a bastion approach
Since we can't directly connect to RDS, this creates a script for indirect methods
"""

import os

print("🔧 Alternative Methods to Create Tables in AWS RDS")
print("=" * 50)
print("\nSince RDS Query Editor doesn't work with regular PostgreSQL instances,")
print("here are your options:\n")

print("1️⃣ OPTION 1: AWS Systems Manager Session Manager")
print("   - Create an EC2 instance in the same VPC as RDS")
print("   - Use Session Manager to connect")
print("   - Run: psql -h farmer-crm-production.cifgmm0mqg5q.us-east-1.rds.amazonaws.com -U postgres -d postgres -f farmer_crm_aws_ready.sql")
print("   - Password: 2hpzvrg_xP~qNbz1[_NppSK$e*O1")

print("\n2️⃣ OPTION 2: AWS Cloud Shell")
print("   - Open AWS Cloud Shell from AWS Console")
print("   - Upload farmer_crm_aws_ready.sql")
print("   - Run the psql command above")

print("\n3️⃣ OPTION 3: Temporary Public Access (Not Recommended)")
print("   - Modify RDS security group to allow your IP")
print("   - Use pgAdmin or DBeaver from your Windows")
print("   - Remove public access after import")

print("\n4️⃣ OPTION 4: Lambda Function")
print("   - Create a Lambda function in the VPC")
print("   - Use it to run the SQL commands")

print("\n5️⃣ OPTION 5: Wait for App Runner")
print("   - The import feature will be available once deployment completes")
print("   - Check: https://6pmgrirjre.us-east-1.awsapprunner.com/database/import")

# Create a smaller test SQL to verify connection
with open('test_connection.sql', 'w') as f:
    f.write("""-- Test SQL for AWS RDS
CREATE TABLE IF NOT EXISTS test_connection (
    id SERIAL PRIMARY KEY,
    message VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO test_connection (message) VALUES ('Database connected successfully!');

SELECT * FROM test_connection;
""")

print("\n📄 Created test_connection.sql to verify your connection works")
print("\n💡 Most practical: Use AWS Cloud Shell or wait for App Runner deployment")