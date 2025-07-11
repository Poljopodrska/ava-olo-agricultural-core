#!/usr/bin/env python3
"""
Extract only data (INSERT statements) from SQL file
"""

import re

print("Extracting data from farmer_crm_full_with_data.sql...")

with open('farmer_crm_full_with_data.sql', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all COPY statements with their data
copy_pattern = r'COPY\s+"public"\."(\w+)"\s*\(([^)]+)\)\s+FROM\s+stdin;\s*(.*?)\\\.'
matches = re.findall(copy_pattern, content, re.DOTALL | re.MULTILINE)

insert_statements = []
total_rows = 0

for table_name, columns, data in matches:
    data = data.strip()
    if data:
        # Parse column names
        col_list = [col.strip().strip('"') for col in columns.split(',')]
        
        # Process each line of data
        lines = data.split('\n')
        row_count = 0
        
        for line in lines:
            if line.strip():
                values = line.split('\t')
                # Convert \N to NULL
                processed_values = []
                for v in values:
                    if v == '\\N':
                        processed_values.append('NULL')
                    else:
                        # Escape single quotes and wrap in quotes
                        v = v.replace("'", "''")
                        processed_values.append(f"'{v}'")
                
                # Create INSERT statement
                insert = f"INSERT INTO {table_name} ({', '.join(col_list)}) VALUES ({', '.join(processed_values)});"
                insert_statements.append(insert)
                row_count += 1
        
        if row_count > 0:
            print(f"  - {table_name}: {row_count} rows")
            total_rows += row_count

# Write to new file
output_file = 'farmer_data_only.sql'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("-- Data only import file\n")
    f.write("-- Generated from farmer_crm_full_with_data.sql\n\n")
    
    for stmt in insert_statements:
        f.write(stmt + '\n')

print(f"\nTotal: {total_rows} INSERT statements")
print(f"Output: {output_file}")
print("\nYou can now upload farmer_data_only.sql to import just the data!")