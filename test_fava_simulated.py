#!/usr/bin/env python3
"""
Simulated FAVA Testing Suite
Tests all database operations with simulated LLM responses
Ensures database operations work correctly
"""
import asyncio
import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.core.database_manager import DatabaseManager

class FAVASimulatedTester:
    """Test suite for FAVA database operations with simulated LLM"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.test_farmer_id = None
        self.test_field_id = None
        self.test_crop_id = None
        self.test_results = []
        
    async def setup_test_farmer(self):
        """Create a test farmer for comprehensive testing"""
        print("[SETUP] Setting up test farmer...")
        
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
    
    def simulate_llm_response(self, message: str) -> Dict:
        """Simulate LLM responses based on message patterns"""
        
        # Field operations
        if "add" in message.lower() and "field" in message.lower():
            if "North Vineyard" in message:
                return {
                    "response": "Adding North Vineyard (4.5 ha) to your farm records",
                    "database_action": "INSERT",
                    "sql_query": f"INSERT INTO fields (farmer_id, field_name, area_ha) VALUES ({self.test_farmer_id}, 'North Vineyard', 4.5) RETURNING id",
                    "needs_confirmation": False
                }
            elif "South Orchard" in message:
                return {
                    "response": "Adding South Orchard (2.8 ha) to your farm records",
                    "database_action": "INSERT",
                    "sql_query": f"INSERT INTO fields (farmer_id, field_name, area_ha) VALUES ({self.test_farmer_id}, 'South Orchard', 2.8) RETURNING id",
                    "needs_confirmation": False
                }
            elif "East Block" in message:
                return {
                    "response": "Adding East Block (3 ha) to your farm records",
                    "database_action": "INSERT",
                    "sql_query": f"INSERT INTO fields (farmer_id, field_name, area_ha) VALUES ({self.test_farmer_id}, 'East Block', 3) RETURNING id",
                    "needs_confirmation": False
                }
        
        # Update field
        elif "actually" in message.lower() and "hectares" in message.lower():
            return {
                "response": "Updating North Vineyard size to 5.2 hectares",
                "database_action": "UPDATE",
                "sql_query": f"UPDATE fields SET area_ha = 5.2 WHERE farmer_id = {self.test_farmer_id} AND field_name = 'North Vineyard'",
                "needs_confirmation": False
            }
        
        # Plant crop
        elif "planted" in message.lower():
            if "Cabernet" in message:
                return {
                    "response": "Recording Cabernet Sauvignon grapes in North Vineyard",
                    "database_action": "INSERT",
                    "sql_query": f"INSERT INTO field_crops (field_id, crop_type, variety, planting_date) VALUES ((SELECT id FROM fields WHERE farmer_id = {self.test_farmer_id} AND field_name = 'North Vineyard'), 'Grapes', 'Cabernet Sauvignon', CURRENT_DATE - INTERVAL '1 day') RETURNING id",
                    "needs_confirmation": False
                }
            elif "mangoes" in message:
                return {
                    "response": "Recording mangoes planted in South Orchard",
                    "database_action": "INSERT",
                    "sql_query": f"INSERT INTO field_crops (field_id, crop_type, variety, planting_date) VALUES ((SELECT id FROM fields WHERE farmer_id = {self.test_farmer_id} AND field_name = 'South Orchard'), 'Mangoes', 'Unknown', CURRENT_DATE) RETURNING id",
                    "needs_confirmation": False
                }
            elif "tomatoes" in message:
                return {
                    "response": "Recording tomatoes in East Block",
                    "database_action": "INSERT",
                    "sql_query": f"INSERT INTO field_crops (field_id, crop_type, variety, planting_date) VALUES ((SELECT id FROM fields WHERE farmer_id = {self.test_farmer_id} AND field_name = 'East Block'), 'Tomatoes', 'Unknown', CURRENT_DATE) RETURNING id",
                    "needs_confirmation": False
                }
        
        # Update crop
        elif "actually Merlot" in message:
            return {
                "response": "Updating grape variety to Merlot",
                "database_action": "UPDATE",
                "sql_query": f"UPDATE field_crops SET variety = 'Merlot' WHERE field_id = (SELECT id FROM fields WHERE farmer_id = {self.test_farmer_id} AND field_name = 'North Vineyard') AND crop_type = 'Grapes'",
                "needs_confirmation": False
            }
        
        # Add tasks
        elif "sprayed" in message.lower() or "irrigated" in message.lower() or "fertilizer" in message.lower():
            if "fungicide" in message.lower():
                return {
                    "response": "Recording fungicide spraying on North Vineyard",
                    "database_action": "INSERT",
                    "sql_query": f"INSERT INTO tasks (field_id, task_type, date_performed, status) VALUES ((SELECT id FROM fields WHERE farmer_id = {self.test_farmer_id} AND field_name = 'North Vineyard'), 'Fungicide Spraying', CURRENT_DATE, 'completed')",
                    "needs_confirmation": False
                }
            elif "irrigated" in message.lower():
                return {
                    "response": "Recording irrigation task for South Orchard",
                    "database_action": "INSERT",
                    "sql_query": f"INSERT INTO tasks (field_id, task_type, date_performed, status) VALUES ((SELECT id FROM fields WHERE farmer_id = {self.test_farmer_id} AND field_name = 'South Orchard'), 'Irrigation - 3 hours', CURRENT_DATE, 'completed')",
                    "needs_confirmation": False
                }
            elif "nitrogen" in message.lower():
                return {
                    "response": "Recording nitrogen fertilizer application",
                    "database_action": "INSERT",
                    "sql_query": f"INSERT INTO tasks (field_id, task_type, date_performed, status) VALUES ((SELECT id FROM fields WHERE farmer_id = {self.test_farmer_id} AND field_name = 'North Vineyard'), 'Nitrogen Fertilizer - 40kg/ha', CURRENT_DATE, 'completed')",
                    "needs_confirmation": False
                }
        
        # Delete operations
        elif "delete" in message.lower() or "remove" in message.lower():
            if "irrigation task" in message.lower():
                return {
                    "response": "Deleting today's irrigation task",
                    "database_action": "DELETE",
                    "sql_query": f"DELETE FROM tasks WHERE field_id IN (SELECT id FROM fields WHERE farmer_id = {self.test_farmer_id}) AND task_type LIKE '%Irrigation%' AND date_performed = CURRENT_DATE",
                    "needs_confirmation": False
                }
            elif "mango crop" in message.lower():
                return {
                    "response": "Removing mango crop from South Orchard",
                    "database_action": "DELETE",
                    "sql_query": f"DELETE FROM field_crops WHERE field_id = (SELECT id FROM fields WHERE farmer_id = {self.test_farmer_id} AND field_name = 'South Orchard') AND crop_type = 'Mangoes'",
                    "needs_confirmation": False
                }
            elif "delete my field" in message.lower():
                return {
                    "response": "Which field would you like to delete?",
                    "database_action": None,
                    "sql_query": None,
                    "needs_confirmation": True,
                    "confirmation_question": "Which field should I delete?"
                }
        
        # Query operations
        elif "what fields" in message.lower() or "tell me about" in message.lower():
            return {
                "response": "You have North Vineyard (5.2 ha), South Orchard (2.8 ha) with grapes and mangoes",
                "database_action": None,
                "sql_query": None,
                "needs_confirmation": False
            }
        
        # Default response
        return {
            "response": "I understand your message about farming",
            "database_action": None,
            "sql_query": None,
            "needs_confirmation": False
        }
    
    async def test_scenario(self, name: str, message: str, expected_action: str = None) -> Dict:
        """Run a single test scenario"""
        print(f"\n[TEST] {name}")
        print(f"   Message: '{message}'")
        
        try:
            # Simulate FAVA response
            result = self.simulate_llm_response(message)
            
            # Display results
            print(f"   Response: {result.get('response', 'No response')[:100]}...")
            
            if result.get('database_action'):
                print(f"   [OK] Database Action: {result['database_action']}")
                
            if result.get('sql_query'):
                print(f"   [SQL] Generated: {result['sql_query'][:150]}...")
                
                # Execute the SQL if not a confirmation request
                if not result.get('needs_confirmation'):
                    try:
                        async with self.db_manager.get_connection_async() as conn:
                            # Handle different query types
                            if result['database_action'] == 'INSERT':
                                if 'RETURNING' in result['sql_query']:
                                    exec_result = await conn.fetchrow(result['sql_query'])
                                    if exec_result:
                                        returned_id = exec_result[0]
                                        print(f"   [OK] Executed INSERT - New ID: {returned_id}")
                                        
                                        # Store IDs for later tests
                                        if 'fields' in result['sql_query']:
                                            self.test_field_id = returned_id
                                        elif 'field_crops' in result['sql_query']:
                                            self.test_crop_id = returned_id
                                else:
                                    await conn.execute(result['sql_query'])
                                    print(f"   [OK] Executed INSERT")
                            elif result['database_action'] == 'UPDATE':
                                await conn.execute(result['sql_query'])
                                print(f"   [OK] Executed UPDATE")
                            elif result['database_action'] == 'DELETE':
                                await conn.execute(result['sql_query'])
                                print(f"   [OK] Executed DELETE")
                            else:
                                exec_result = await conn.fetch(result['sql_query'])
                                print(f"   [OK] Query returned {len(exec_result)} rows")
                                
                    except Exception as sql_error:
                        print(f"   [FAIL] SQL Execution Failed: {sql_error}")
                        result['execution_failed'] = str(sql_error)
            
            if result.get('needs_confirmation'):
                print(f"   [?] Confirmation Needed: {result.get('confirmation_question')}")
            
            # Check expected action
            success = True
            if expected_action:
                if result.get('database_action') != expected_action:
                    print(f"   [FAIL] Expected {expected_action}, got {result.get('database_action')}")
                    success = False
                else:
                    print(f"   [OK] Correct action detected")
            
            self.test_results.append({
                'name': name,
                'success': success and not result.get('execution_failed'),
                'result': result
            })
            
            return result
            
        except Exception as e:
            print(f"   [FAIL] Test Error: {str(e)}")
            self.test_results.append({
                'name': name,
                'success': False,
                'error': str(e)
            })
            return {'error': str(e)}
    
    async def run_comprehensive_tests(self):
        """Run all test scenarios"""
        print("\n" + "="*60)
        print("FAVA SIMULATED DATABASE TESTING")
        print("="*60)
        
        # Setup
        await self.setup_test_farmer()
        
        # TEST GROUP 1: FIELD OPERATIONS
        print("\n" + "-"*60)
        print("[GROUP] TESTING FIELD OPERATIONS")
        print("-"*60)
        
        await self.test_scenario(
            "Add New Field",
            "I want to add a new field called North Vineyard, it's 4.5 hectares",
            expected_action="INSERT"
        )
        
        await self.test_scenario(
            "Add Field with Location",
            "Add my South Orchard field, 2.8 hectares, near the river",
            expected_action="INSERT"
        )
        
        await self.test_scenario(
            "Update Field Size",
            "Actually North Vineyard is 5.2 hectares, not 4.5",
            expected_action="UPDATE"
        )
        
        # TEST GROUP 2: CROP OPERATIONS
        print("\n" + "-"*60)
        print("[GROUP] TESTING CROP OPERATIONS")
        print("-"*60)
        
        await self.test_scenario(
            "Plant Crop in Field",
            "I planted Cabernet Sauvignon grapes in North Vineyard yesterday",
            expected_action="INSERT"
        )
        
        await self.test_scenario(
            "Plant Second Crop",
            "Today I planted mangoes in the South Orchard",
            expected_action="INSERT"
        )
        
        await self.test_scenario(
            "Update Crop Variety",
            "The grapes in North Vineyard are actually Merlot, not Cabernet",
            expected_action="UPDATE"
        )
        
        # TEST GROUP 3: TASK OPERATIONS
        print("\n" + "-"*60)
        print("[GROUP] TESTING TASK OPERATIONS")
        print("-"*60)
        
        await self.test_scenario(
            "Add Spraying Task",
            "I sprayed fungicide on the North Vineyard this morning",
            expected_action="INSERT"
        )
        
        await self.test_scenario(
            "Add Irrigation Task",
            "Irrigated South Orchard for 3 hours today",
            expected_action="INSERT"
        )
        
        await self.test_scenario(
            "Add Fertilization Task",
            "Applied nitrogen fertilizer to North Vineyard at 40kg per hectare",
            expected_action="INSERT"
        )
        
        # TEST GROUP 4: DELETION OPERATIONS
        print("\n" + "-"*60)
        print("[GROUP] TESTING DELETION OPERATIONS")
        print("-"*60)
        
        await self.test_scenario(
            "Delete Task",
            "Delete the irrigation task from today",
            expected_action="DELETE"
        )
        
        await self.test_scenario(
            "Remove Crop",
            "Remove the mango crop from South Orchard",
            expected_action="DELETE"
        )
        
        # TEST GROUP 5: COMPLEX SCENARIOS
        print("\n" + "-"*60)
        print("[GROUP] TESTING COMPLEX SCENARIOS")
        print("-"*60)
        
        await self.test_scenario(
            "Complex Multi-Operation",
            "I have a new 3 hectare field called East Block where I just planted tomatoes",
            expected_action="INSERT"
        )
        
        await self.test_scenario(
            "Ambiguous Deletion",
            "Delete my field",
            expected_action=None  # Should ask which field
        )
        
        # FINAL VERIFICATION
        print("\n" + "-"*60)
        print("[VERIFY] FINAL DATABASE VERIFICATION")
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
        print("[SUMMARY] TEST RESULTS")
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
                    print(f"      [FAIL] {result['name']}")
                    if 'error' in result:
                        print(f"         Error: {result['error']}")
        
        print("\n" + "="*60)
        if successful == total:
            print("[SUCCESS] ALL TESTS PASSED! FAVA database operations working correctly!")
        else:
            print(f"[WARNING] {total - successful} tests failed. Review and fix issues.")
        print("="*60)
        
        return {
            'total': total,
            'successful': successful,
            'failed': total - successful,
            'success_rate': (successful/total)*100 if total > 0 else 0
        }

async def main():
    """Run simulated FAVA tests"""
    
    print("[INFO] Running FAVA tests with simulated LLM responses")
    print("[INFO] This tests database operations without requiring OpenAI API")
    
    # Run tests
    tester = FAVASimulatedTester()
    results = await tester.run_comprehensive_tests()
    
    # Exit with appropriate code
    if results['failed'] == 0:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())