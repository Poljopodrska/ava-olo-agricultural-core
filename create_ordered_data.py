#!/usr/bin/env python3
"""
Create ordered data import file respecting foreign key constraints
"""

import re

print("Creating ordered data import file...")

# Define table import order based on dependencies
table_order = [
    # Independent tables first
    'farmers',
    'crop_nutrient_needs',
    'crop_technology',
    'fertilizers',
    'cp_products',
    'material_catalog',
    'task_types',
    'conversation_state',
    'conversation_states',
    'weather_data',
    
    # Tables that depend on farmers
    'fields',
    'incoming_messages',
    'pending_messages',
    'invoices',
    'inventory',
    
    # Tables that depend on fields
    'field_crops',
    'field_soil_data',
    'fertilizing_plans',
    'growth_stage_reports',
    'tasks',
    
    # Tables that depend on tasks
    'task_fields',
    'task_material_dose',
    'inventory_deductions',
]

# Read the data file
with open('farmer_data_only.sql', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Group statements by table
table_statements = {}
for line in lines:
    if line.startswith('INSERT INTO'):
        # Extract table name
        match = re.match(r'INSERT INTO (\w+)', line)
        if match:
            table_name = match.group(1)
            if table_name not in table_statements:
                table_statements[table_name] = []
            table_statements[table_name].append(line.strip())

# Write ordered file
output_file = 'farmer_data_ordered.sql'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("-- Ordered data import file\n")
    f.write("-- Respects foreign key constraints\n\n")
    
    total_statements = 0
    
    for table in table_order:
        if table in table_statements:
            f.write(f"\n-- {table} ({len(table_statements[table])} rows)\n")
            for stmt in table_statements[table]:
                f.write(stmt + '\n')
            total_statements += len(table_statements[table])
            print(f"  ✓ {table}: {len(table_statements[table])} rows")
    
    # Add any tables not in our order list
    for table, statements in table_statements.items():
        if table not in table_order:
            f.write(f"\n-- {table} ({len(statements)} rows)\n")
            for stmt in statements:
                f.write(stmt + '\n')
            total_statements += len(statements)
            print(f"  ✓ {table}: {len(statements)} rows (added)")

print(f"\nTotal: {total_statements} INSERT statements")
print(f"Output: {output_file}")
print("\nUpload farmer_data_ordered.sql to import data in the correct order!")