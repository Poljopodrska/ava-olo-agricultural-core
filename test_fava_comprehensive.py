#!/usr/bin/env python3
"""
Comprehensive FAVA Testing Suite
Tests all database operations: fields, crops, tasks, updates, deletions
Ensures LLM correctly generates SQL for all scenarios
"""
import asyncio
import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.cava.fava_engine import get_fava_engine
from modules.core.database_manager import DatabaseManager

class FAVAComprehensiveTester:
    """Test suite for FAVA database operations"""
    
    def __init__(self):
        self.fava = get_fava_engine()
        self.db_manager = DatabaseManager()
        self.test_farmer_id = None
        self.test_field_id = None
        self.test_crop_id = None
        self.test_results = []
        
    async def setup_test_farmer(self):
        """Create a test farmer for comprehensive testing"""
        print("🔧 Setting up test farmer...")
        
        async with self.db_manager.get_connection_async() as conn:
            # Check if test farmer exists
            existing = await conn.fetchrow(
                "SELECT id FROM farmers WHERE wa_phone_number = $1",
                "+999888777666"
            )
            
            if existing:
                self.test_farmer_id = existing['id']
                print(f"   Using existing test farmer ID: {self.test_farmer_id}")
                # Clean up any existing test data
                await self.cleanup_test_data(conn)
            else:
                # Create test farmer
                result = await conn.fetchrow(
                    """INSERT INTO farmers (
                        manager_name, manager_last_name, wa_phone_number, 
                        phone, email, farm_name, city, country
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8) 
                    RETURNING id""",
                    "Test", "Farmer", "+999888777666", "+999888777666",
                    "test@fava.com", "FAVA Test Farm", "Sofia", "Bulgaria"
                )
                self.test_farmer_id = result['id']
                print(f"   Created test farmer ID: {self.test_farmer_id}")
    
    async def cleanup_test_data(self, conn):
        """Clean up existing test data for fresh start"""
        print("   Cleaning up existing test data...")
        
        # Delete in reverse order of dependencies
        await conn.execute("""
            DELETE FROM tasks 
            WHERE field_id IN (
                SELECT id FROM fields WHERE farmer_id = $1
            )
        """, self.test_farmer_id)
        
        await conn.execute("""
            DELETE FROM field_crops 
            WHERE field_id IN (
                SELECT id FROM fields WHERE farmer_id = $1
            )
        """, self.test_farmer_id)
        
        await conn.execute(
            "DELETE FROM fields WHERE farmer_id = $1",
            self.test_farmer_id
        )
        
        print("   Cleanup complete")
    
    async def test_scenario(self, name: str, message: str, expected_action: str = None) -> Dict:
        """Run a single test scenario"""
        print(f"\n📝 Test: {name}")
        print(f"   Message: '{message}'")
        
        try:
            async with self.db_manager.get_connection_async() as conn:
                result = await self.fava.process_farmer_message(
                    farmer_id=self.test_farmer_id,
                    message=message,
                    db_connection=conn
                )
                
                # Display results
                print(f"   Response: {result.get('response', 'No response')[:100]}...")
                
                if result.get('database_action'):
                    print(f"   ✅ Database Action: {result['database_action']}")
                    
                if result.get('sql_query'):
                    print(f"   📊 SQL Generated: {result['sql_query'][:150]}...")
                    
                    # Execute the SQL if not a confirmation request
                    if not result.get('needs_confirmation'):
                        try:
                            # Handle different query types
                            if result['database_action'] == 'INSERT':
                                if 'RETURNING' in result['sql_query']:
                                    exec_result = await conn.fetchrow(result['sql_query'])
                                    if exec_result:
                                        returned_id = exec_result[0]
                                        print(f"   ✅ Executed INSERT - New ID: {returned_id}")
                                        
                                        # Store IDs for later tests
                                        if 'fields' in result['sql_query']:
                                            self.test_field_id = returned_id
                                        elif 'field_crops' in result['sql_query']:
                                            self.test_crop_id = returned_id
                                else:
                                    await conn.execute(result['sql_query'])
                                    print(f"   ✅ Executed INSERT")
                            elif result['database_action'] == 'UPDATE':
                                await conn.execute(result['sql_query'])
                                print(f"   ✅ Executed UPDATE")
                            elif result['database_action'] == 'DELETE':
                                await conn.execute(result['sql_query'])
                                print(f"   ✅ Executed DELETE")
                            else:
                                exec_result = await conn.fetch(result['sql_query'])
                                print(f"   ✅ Query returned {len(exec_result)} rows")
                                
                        except Exception as sql_error:
                            print(f"   ❌ SQL Execution Failed: {sql_error}")
                            result['execution_failed'] = str(sql_error)
                
                if result.get('needs_confirmation'):
                    print(f"   ❓ Confirmation Needed: {result.get('confirmation_question')}")
                
                # Check expected action
                success = True
                if expected_action:
                    if result.get('database_action') != expected_action:
                        print(f"   ❌ Expected {expected_action}, got {result.get('database_action')}")
                        success = False
                    else:
                        print(f"   ✅ Correct action detected")
                
                # Verify in database
                if result.get('database_action') == 'INSERT' and 'fields' in result.get('sql_query', ''):
                    # Verify field was created
                    field_check = await conn.fetchrow(
                        "SELECT * FROM fields WHERE farmer_id = $1 ORDER BY id DESC LIMIT 1",
                        self.test_farmer_id
                    )
                    if field_check:
                        print(f"   ✅ Verified: Field '{field_check['field_name']}' exists in database")
                        self.test_field_id = field_check['id']
                
                self.test_results.append({
                    'name': name,
                    'success': success and not result.get('execution_failed'),
                    'result': result
                })
                
                return result
                
        except Exception as e:
            print(f"   ❌ Test Error: {str(e)}")
            self.test_results.append({
                'name': name,
                'success': False,
                'error': str(e)
            })
            return {'error': str(e)}
    
    async def run_comprehensive_tests(self):
        """Run all test scenarios"""
        print("\n" + "="*60)
        print("🚀 FAVA COMPREHENSIVE DATABASE TESTING")
        print("="*60)
        
        # Setup
        await self.setup_test_farmer()
        
        # TEST GROUP 1: FIELD OPERATIONS
        print("\n" + "-"*60)
        print("📍 TESTING FIELD OPERATIONS")
        print("-"*60)
        
        # Test 1: Add new field
        await self.test_scenario(
            "Add New Field",
            "I want to add a new field called North Vineyard, it's 4.5 hectares",
            expected_action="INSERT"
        )
        
        # Test 2: Add another field with more details
        await self.test_scenario(
            "Add Field with Location",
            "Add my South Orchard field, 2.8 hectares, near the river",
            expected_action="INSERT"
        )
        
        # Test 3: Update field size
        await self.test_scenario(
            "Update Field Size",
            "Actually North Vineyard is 5.2 hectares, not 4.5",
            expected_action="UPDATE"
        )
        
        # Test 4: Ambiguous field mention
        await self.test_scenario(
            "Ambiguous Field Mention",
            "My greenhouse is 600 square meters",
            expected_action=None  # Should ask for confirmation
        )
        
        # TEST GROUP 2: CROP OPERATIONS
        print("\n" + "-"*60)
        print("🌱 TESTING CROP OPERATIONS")
        print("-"*60)
        
        # Test 5: Plant crop in field
        await self.test_scenario(
            "Plant Crop in Field",
            "I planted Cabernet Sauvignon grapes in North Vineyard yesterday",
            expected_action="INSERT"
        )
        
        # Test 6: Plant another crop
        await self.test_scenario(
            "Plant Second Crop",
            "Today I planted mangoes in the South Orchard",
            expected_action="INSERT"
        )
        
        # Test 7: Update crop variety
        await self.test_scenario(
            "Update Crop Variety",
            "The grapes in North Vineyard are actually Merlot, not Cabernet",
            expected_action="UPDATE"
        )
        
        # TEST GROUP 3: TASK OPERATIONS
        print("\n" + "-"*60)
        print("📋 TESTING TASK OPERATIONS")
        print("-"*60)
        
        # Test 8: Add spraying task
        await self.test_scenario(
            "Add Spraying Task",
            "I sprayed fungicide on the North Vineyard this morning",
            expected_action="INSERT"
        )
        
        # Test 9: Add irrigation task
        await self.test_scenario(
            "Add Irrigation Task",
            "Irrigated South Orchard for 3 hours today",
            expected_action="INSERT"
        )
        
        # Test 10: Add fertilization task
        await self.test_scenario(
            "Add Fertilization Task",
            "Applied nitrogen fertilizer to North Vineyard at 40kg per hectare",
            expected_action="INSERT"
        )
        
        # TEST GROUP 4: QUERY OPERATIONS
        print("\n" + "-"*60)
        print("🔍 TESTING QUERY OPERATIONS")
        print("-"*60)
        
        # Test 11: Ask about fields
        await self.test_scenario(
            "Query Fields",
            "What fields do I have?",
            expected_action=None  # Should just respond with info
        )
        
        # Test 12: Ask about specific field
        await self.test_scenario(
            "Query Specific Field",
            "Tell me about my North Vineyard",
            expected_action=None
        )
        
        # TEST GROUP 5: DELETION OPERATIONS
        print("\n" + "-"*60)
        print("🗑️ TESTING DELETION OPERATIONS")
        print("-"*60)
        
        # Test 13: Delete a task
        await self.test_scenario(
            "Delete Task",
            "Delete the irrigation task from today",
            expected_action="DELETE"
        )
        
        # Test 14: Remove a crop
        await self.test_scenario(
            "Remove Crop",
            "Remove the mango crop from South Orchard",
            expected_action="DELETE"
        )
        
        # TEST GROUP 6: COMPLEX SCENARIOS
        print("\n" + "-"*60)
        print("🔧 TESTING COMPLEX SCENARIOS")
        print("-"*60)
        
        # Test 15: Multiple operations in one message
        await self.test_scenario(
            "Complex Multi-Operation",
            "I have a new 3 hectare field called East Block where I just planted tomatoes",
            expected_action="INSERT"  # Should handle both field and crop
        )
        
        # Test 16: Contextual reference
        await self.test_scenario(
            "Contextual Reference",
            "The tomatoes there need watering",
            expected_action=None  # Should understand "there" refers to East Block
        )
        
        # TEST GROUP 7: ERROR HANDLING
        print("\n" + "-"*60)
        print("❌ TESTING ERROR HANDLING")
        print("-"*60)
        
        # Test 17: Invalid field reference
        await self.test_scenario(
            "Invalid Field Reference",
            "I planted corn in the Moon Base field",
            expected_action=None  # Should handle non-existent field gracefully
        )
        
        # Test 18: Ambiguous deletion
        await self.test_scenario(
            "Ambiguous Deletion",
            "Delete my field",
            expected_action=None  # Should ask which field
        )
        
        # FINAL VERIFICATION
        print("\n" + "-"*60)
        print("✅ FINAL DATABASE VERIFICATION")
        print("-"*60)
        
        async with self.db_manager.get_connection_async() as conn:
            # Check fields
            fields = await conn.fetch(
                "SELECT * FROM fields WHERE farmer_id = $1",
                self.test_farmer_id
            )
            print(f"   Fields in database: {len(fields)}")
            for field in fields:
                print(f"      - {field['field_name']}: {field['area_ha']} ha")
            
            # Check crops
            if fields:
                field_ids = [f['id'] for f in fields]
                crops = await conn.fetch(
                    "SELECT fc.*, f.field_name FROM field_crops fc "
                    "JOIN fields f ON fc.field_id = f.id "
                    "WHERE fc.field_id = ANY($1)",
                    field_ids
                )
                print(f"   Crops in database: {len(crops)}")
                for crop in crops:
                    print(f"      - {crop['crop_type']} ({crop['variety']}) in {crop['field_name']}")
            
            # Check tasks
            if fields:
                tasks = await conn.fetch(
                    "SELECT t.*, f.field_name FROM tasks t "
                    "JOIN fields f ON t.field_id = f.id "
                    "WHERE t.field_id = ANY($1)",
                    field_ids
                )
                print(f"   Tasks in database: {len(tasks)}")
                for task in tasks:
                    print(f"      - {task['task_type']} in {task['field_name']}")
        
        # SUMMARY
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        successful = sum(1 for r in self.test_results if r['success'])
        total = len(self.test_results)
        
        print(f"   Total Tests: {total}")
        print(f"   Successful: {successful}")
        print(f"   Failed: {total - successful}")
        print(f"   Success Rate: {(successful/total)*100:.1f}%")
        
        if total - successful > 0:
            print("\n   Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"      ❌ {result['name']}")
                    if 'error' in result:
                        print(f"         Error: {result['error']}")
        
        print("\n" + "="*60)
        if successful == total:
            print("🎉 ALL TESTS PASSED! FAVA is working correctly!")
        else:
            print(f"⚠️  {total - successful} tests failed. Review and fix issues.")
        print("="*60)
        
        return {
            'total': total,
            'successful': successful,
            'failed': total - successful,
            'success_rate': (successful/total)*100 if total > 0 else 0
        }

async def main():
    """Run comprehensive FAVA tests"""
    
    # Check for API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not set. FAVA requires OpenAI API access.")
        sys.exit(1)
    
    # Run tests
    tester = FAVAComprehensiveTester()
    results = await tester.run_comprehensive_tests()
    
    # Exit with appropriate code
    if results['failed'] == 0:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())