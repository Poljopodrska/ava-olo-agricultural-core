#!/usr/bin/env python3
"""
AVA OLO Database Access Helper for Claude Code
Provides secure, read-only access to farmer database through ECS ALB endpoints
"""

import requests
import json
from typing import Dict, List, Any, Optional

class AVADatabaseAccess:
    """
    Helper class for Claude Code to access AVA OLO database
    Uses ECS ALB endpoint with secure authentication
    """
    
    def __init__(self, base_url: str = None, dev_key: str = None):
        """
        Initialize database access helper
        
        Args:
            base_url: Base URL (defaults to ECS ALB)
            dev_key: Development access key
        """
        self.base_url = base_url or "http://ava-olo-alb-65365776.us-east-1.elb.amazonaws.com"
        self.dev_key = dev_key or "ava-dev-2025-secure-key"
        self.headers = {
            "X-Dev-Key": self.dev_key,
            "Content-Type": "application/json"
        }
        self.timeout = 30
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get complete database schema
        
        Returns:
            Schema information including all tables and columns
        """
        try:
            response = requests.get(
                f"{self.base_url}/dev/db/schema", 
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Request failed: {str(e)}"}
    
    def query(self, sql: str) -> Dict[str, Any]:
        """
        Execute SELECT query and return results
        
        Args:
            sql: SELECT query to execute
            
        Returns:
            Query results with rows and metadata
        """
        if not sql.strip().upper().startswith('SELECT'):
            return {"success": False, "error": "Only SELECT queries allowed"}
        
        try:
            response = requests.post(
                f"{self.base_url}/dev/db/query",
                headers=self.headers,
                json={"query": sql},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Request failed: {str(e)}"}
    
    def get_tables(self) -> Dict[str, Any]:
        """
        Get all tables with row counts
        
        Returns:
            List of tables with column and row counts
        """
        try:
            response = requests.get(
                f"{self.base_url}/dev/db/tables", 
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Request failed: {str(e)}"}
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific table
        
        Args:
            table_name: Name of the table
            
        Returns:
            Table structure and sample data
        """
        schema = self.get_schema()
        if not schema.get('success'):
            return schema
        
        if table_name not in schema.get('schema', {}):
            return {"success": False, "error": f"Table '{table_name}' not found"}
        
        # Get sample data
        sample = self.query(f"SELECT * FROM {table_name} LIMIT 3")
        
        return {
            "success": True,
            "table_name": table_name,
            "structure": schema['schema'][table_name],
            "sample_data": sample.get('rows', []) if sample.get('success') else []
        }
    
    # Convenience methods for common farmer queries
    def count_farmers(self) -> int:
        """Get total farmer count"""
        result = self.query("SELECT COUNT(*) as count FROM ava_farmers")
        if result.get('success') and result.get('rows'):
            return result['rows'][0].get('count', 0)
        return 0
    
    def get_farmer_overview(self) -> Dict[str, Any]:
        """Get comprehensive farmer statistics"""
        return self.query("""
            SELECT 
                COUNT(*) as total_farmers,
                COUNT(DISTINCT city) as cities_covered,
                SUM(total_hectares) as total_hectares,
                AVG(total_hectares) as avg_hectares_per_farmer,
                COUNT(DISTINCT farmer_type) as farmer_types
            FROM ava_farmers
            WHERE total_hectares IS NOT NULL
        """)
    
    def get_recent_registrations(self, limit: int = 10) -> Dict[str, Any]:
        """Get recent farmer registrations"""
        return self.query(f"""
            SELECT 
                manager_name,
                manager_last_name,
                farm_name,
                city,
                total_hectares,
                farmer_type,
                created_at
            FROM ava_farmers
            ORDER BY created_at DESC
            LIMIT {limit}
        """)
    
    def get_crop_distribution(self) -> Dict[str, Any]:
        """Get distribution of crops across fields"""
        return self.query("""
            SELECT 
                fc.crop_name,
                COUNT(*) as field_count,
                SUM(f.field_size) as total_hectares
            FROM ava_field_crops fc
            JOIN ava_fields f ON fc.field_id = f.field_id
            WHERE fc.status = 'active'
            GROUP BY fc.crop_name
            ORDER BY total_hectares DESC
        """)
    
    def get_conversation_topics(self) -> Dict[str, Any]:
        """Get most common conversation topics"""
        return self.query("""
            SELECT 
                topic,
                COUNT(*) as conversation_count
            FROM ava_conversations 
            WHERE topic IS NOT NULL
            GROUP BY topic
            ORDER BY conversation_count DESC
            LIMIT 10
        """)
    
    def search_farmers(self, search_term: str) -> Dict[str, Any]:
        """
        Search farmers by name or farm name
        
        Args:
            search_term: Search term for farmer or farm name
            
        Returns:
            Matching farmers
        """
        return self.query(f"""
            SELECT 
                manager_name,
                manager_last_name,
                farm_name,
                city,
                total_hectares,
                farmer_type
            FROM ava_farmers
            WHERE 
                LOWER(manager_name) LIKE LOWER('%{search_term}%') OR
                LOWER(manager_last_name) LIKE LOWER('%{search_term}%') OR
                LOWER(farm_name) LIKE LOWER('%{search_term}%')
            ORDER BY manager_last_name, manager_name
            LIMIT 20
        """)

def print_query_results(result: Dict[str, Any], title: str = "Query Results"):
    """
    Pretty print database query results
    
    Args:
        result: Result dictionary from query
        title: Title for the output
    """
    print(f"\n=== {title} ===")
    
    if result.get('success'):
        if 'rows' in result:
            rows = result['rows']
            count = result.get('count', len(rows))
            print(f"✅ Query successful ({count} rows)")
            
            if rows:
                # Print column headers
                columns = list(rows[0].keys())
                print(f"\nColumns: {', '.join(columns)}")
                print("-" * 80)
                
                # Print rows
                for i, row in enumerate(rows, 1):
                    print(f"{i:3d}: {dict(row)}")
            else:
                print("No data returned")
        else:
            print("✅ Request successful")
            for key, value in result.items():
                if key != 'success':
                    print(f"{key}: {value}")
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")

# Example usage and testing
if __name__ == "__main__":
    print("=== AVA OLO Database Access Helper ===\n")
    
    # Initialize helper
    db = AVADatabaseAccess()
    
    # Test connection with tables endpoint
    print("🔗 Testing connection...")
    tables = db.get_tables()
    if tables.get('success'):
        print(f"✅ Connected! Found {tables['count']} tables")
        print("Available tables:")
        for table in tables['tables'][:10]:  # Show first 10
            print(f"  - {table['name']} ({table['columns']} columns, {table['rows']} rows)")
    else:
        print(f"❌ Connection failed: {tables.get('error')}")
        exit(1)
    
    # Test farmer overview
    print_query_results(db.get_farmer_overview(), "Farmer Overview")
    
    # Test recent registrations
    print_query_results(db.get_recent_registrations(5), "Recent Registrations")
    
    # Test conversation topics
    print_query_results(db.get_conversation_topics(), "Popular Topics")
    
    print("\n✅ Database access helper is working correctly!")
    print(f"📊 Base URL: {db.base_url}")
    print("🔑 Use ava_database_helper.AVADatabaseAccess() in your code")