#!/usr/bin/env python3
"""
Development Database Helper for Claude Code
Provides easy access to database through monitoring API endpoints
"""

import requests
import json
import os
from typing import Dict, List, Any, Optional

# Import ECS-first configuration
try:
    from ecs_config import get_dev_db_url
    ECS_AVAILABLE = True
except ImportError:
    ECS_AVAILABLE = False
    def get_dev_db_url():
        return "https://bcibj8ws3x.us-east-1.awsapprunner.com"  # Fallback

class DevDatabaseHelper:
    def __init__(self, base_url: str = None, dev_key: str = None):
        """
        Initialize the development database helper
        
        Args:
            base_url: Base URL of the monitoring service (defaults to ECS endpoint)
            dev_key: Development access key (defaults to environment variable)
        """
        if base_url:
            self.base_url = base_url
        else:
            # Use ECS-first configuration
            self.base_url = get_dev_db_url()
            if ECS_AVAILABLE:
                print(f"✅ Using ECS-first endpoint: {self.base_url}")
            else:
                print(f"⚠️  ECS config not available, using App Runner fallback: {self.base_url}")
        self.dev_key = dev_key or os.getenv('DEV_ACCESS_KEY', 'temporary-dev-key-2025')
        self.headers = {
            "X-Dev-Key": self.dev_key,
            "Content-Type": "application/json"
        }
    
    def query(self, sql: str) -> Dict[str, Any]:
        """
        Execute a SELECT query on the database
        
        Args:
            sql: SELECT query to execute
            
        Returns:
            Dictionary with query results
        """
        if not sql.strip().upper().startswith('SELECT'):
            raise ValueError("Only SELECT queries are allowed")
        
        try:
            response = requests.post(
                f"{self.base_url}/dev/db/query",
                headers=self.headers,
                json={"query": sql},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get complete database schema information
        
        Returns:
            Dictionary with schema information
        """
        try:
            response = requests.get(
                f"{self.base_url}/dev/db/schema",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }
    
    def list_tables(self) -> Dict[str, Any]:
        """
        Get list of all database tables with basic info
        
        Returns:
            Dictionary with tables information
        """
        try:
            response = requests.get(
                f"{self.base_url}/dev/db/tables",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }
    
    def describe_table(self, table_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific table
        
        Args:
            table_name: Name of the table to describe
            
        Returns:
            Dictionary with table structure
        """
        schema = self.get_schema()
        if not schema.get('success'):
            return schema
        
        if table_name in schema['schema']:
            return {
                "success": True,
                "table": table_name,
                "details": schema['schema'][table_name]
            }
        else:
            return {
                "success": False,
                "error": f"Table '{table_name}' not found"
            }
    
    def count_rows(self, table_name: str) -> Dict[str, Any]:
        """
        Count rows in a specific table
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with row count
        """
        return self.query(f"SELECT COUNT(*) as row_count FROM {table_name}")
    
    def sample_data(self, table_name: str, limit: int = 5) -> Dict[str, Any]:
        """
        Get sample data from a table
        
        Args:
            table_name: Name of the table
            limit: Number of rows to fetch (default 5)
            
        Returns:
            Dictionary with sample data
        """
        return self.query(f"SELECT * FROM {table_name} LIMIT {limit}")
    
    def farmers_overview(self) -> Dict[str, Any]:
        """
        Get overview of farmers data
        
        Returns:
            Dictionary with farmers overview
        """
        return self.query("""
        SELECT 
            COUNT(*) as total_farmers,
            COUNT(DISTINCT city) as cities,
            SUM(total_hectares) as total_hectares,
            AVG(total_hectares) as avg_hectares_per_farmer
        FROM ava_farmers
        """)
    
    def recent_activity(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get recent activity across all tables
        
        Args:
            hours: Number of hours to look back (default 24)
            
        Returns:
            Dictionary with recent activity
        """
        return self.query(f"""
        SELECT 
            'conversations' as activity_type,
            COUNT(*) as count
        FROM ava_conversations 
        WHERE created_at > NOW() - INTERVAL '{hours} hours'
        
        UNION ALL
        
        SELECT 
            'fields' as activity_type,
            COUNT(*) as count
        FROM ava_fields 
        WHERE created_at > NOW() - INTERVAL '{hours} hours'
        
        UNION ALL
        
        SELECT 
            'tasks' as activity_type,
            COUNT(*) as count
        FROM farm_tasks 
        WHERE created_at > NOW() - INTERVAL '{hours} hours'
        """)

def print_results(result: Dict[str, Any]):
    """
    Pretty print database query results
    
    Args:
        result: Result dictionary from query
    """
    if result.get('success'):
        if 'rows' in result:
            print(f"✅ Query executed successfully ({result['count']} rows)")
            print(f"Columns: {', '.join(result['columns'])}")
            print("\nResults:")
            for i, row in enumerate(result['rows'], 1):
                print(f"{i:3d}: {row}")
        else:
            print(f"✅ Request successful")
            print(json.dumps(result, indent=2, default=str))
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")

# Example usage for Claude Code
if __name__ == "__main__":
    # Initialize helper
    db = DevDatabaseHelper()
    
    print("=== AVA OLO Development Database Helper ===\n")
    
    # List all tables
    print("📋 Available Tables:")
    tables = db.list_tables()
    if tables.get('success'):
        for table in tables['tables']:
            print(f"  - {table['name']} ({table['columns']} columns, {table['rows']} rows)")
    else:
        print(f"Error: {tables.get('error')}")
    
    print("\n" + "="*50)
    
    # Example queries
    examples = [
        ("Farmers Overview", "SELECT COUNT(*) as farmers, SUM(total_hectares) as total_ha FROM ava_farmers"),
        ("Recent Conversations", "SELECT COUNT(*) as recent_conversations FROM ava_conversations WHERE created_at > NOW() - INTERVAL '7 days'"),
        ("Field Distribution", "SELECT COUNT(*) as fields, AVG(field_size) as avg_size FROM ava_fields")
    ]
    
    for name, query in examples:
        print(f"\n📊 {name}:")
        result = db.query(query)
        print_results(result)