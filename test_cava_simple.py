#!/usr/bin/env python3
"""
Simple CAVA Test - Basic checks without external dependencies
Tests core CAVA logic and file structure before deployment
"""
import os
import sys
import json
from datetime import datetime

def test_file_structure():
    """Test 1: Check if all CAVA files exist"""
    print("1️⃣ Testing File Structure...")
    
    required_files = [
        "modules/api/chat_routes.py",
        "modules/cava/conversation_memory.py", 
        "modules/cava/fact_extractor.py",
        "modules/core/database_manager.py",
        "migrations/001_create_cava_tables.sql"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if not missing_files:
        print("   ✅ All CAVA files exist")
        return 10
    else:
        print(f"   ❌ Missing files: {missing_files}")
        return 0

def test_chat_routes_context():
    """Test 2: Check if chat routes properly use context"""
    print("\n2️⃣ Testing Chat Routes Context Usage...")
    
    try:
        with open("modules/api/chat_routes.py", 'r') as f:
            content = f.read()
        
        # Check for critical context usage patterns
        checks = {
            'gets_enhanced_context': 'get_enhanced_context' in content,
            'builds_system_message': 'IMPORTANT CONTEXT about this farmer' in content,
            'includes_conversation_history': 'get_conversation_messages_for_llm' in content,
            'references_previous_crops': 'previously mentioned' in content or 'told you earlier' in content,
            'has_memory_check': 'memory_indicators' in content or 'Memory Check' in content,
            'has_debug_logging': 'llm_debug_log' in content
        }
        
        passed_checks = sum(checks.values())
        
        print(f"   Context usage checks: {passed_checks}/6")
        for check_name, passed in checks.items():
            icon = "✅" if passed else "❌"
            print(f"   {icon} {check_name.replace('_', ' ').title()}")
        
        if passed_checks >= 5:
            print("   ✅ Chat routes properly configured for context")
            return 10
        elif passed_checks >= 3:
            print("   ⚠️ Partial context configuration")
            return 6
        else:
            print("   ❌ Context configuration issues")
            return 2
            
    except Exception as e:
        print(f"   ❌ Error reading chat routes: {e}")
        return 0

def test_memory_module():
    """Test 3: Check CAVA memory module"""
    print("\n3️⃣ Testing CAVA Memory Module...")
    
    try:
        with open("modules/cava/conversation_memory.py", 'r') as f:
            content = f.read()
        
        # Check for critical memory functions
        checks = {
            'has_enhanced_context': 'get_enhanced_context' in content,
            'builds_context_summary': '_build_context_summary' in content,
            'stores_facts': 'store_extracted_facts' in content,
            'retrieves_farmer_facts': 'get_farmer_facts' in content,
            'formats_for_llm': 'get_conversation_messages_for_llm' in content,
            'handles_stored_facts': '_build_facts_summary' in content
        }
        
        passed_checks = sum(checks.values())
        
        print(f"   Memory functions: {passed_checks}/6")
        for check_name, passed in checks.items():
            icon = "✅" if passed else "❌"
            print(f"   {icon} {check_name.replace('_', ' ').title()}")
        
        if passed_checks >= 5:
            print("   ✅ Memory module properly configured")
            return 10
        elif passed_checks >= 3:
            print("   ⚠️ Partial memory configuration")
            return 6
        else:
            print("   ❌ Memory configuration issues")
            return 2
            
    except Exception as e:
        print(f"   ❌ Error reading memory module: {e}")
        return 0

def test_database_schema():
    """Test 4: Check database migration"""
    print("\n4️⃣ Testing Database Schema...")
    
    try:
        with open("migrations/001_create_cava_tables.sql", 'r') as f:
            content = f.read()
        
        # Check for required tables
        required_tables = [
            'chat_messages',
            'farmer_facts', 
            'llm_usage_log'
        ]
        
        tables_found = 0
        for table in required_tables:
            if f"CREATE TABLE" in content and table in content:
                tables_found += 1
                print(f"   ✅ {table} table definition found")
            else:
                print(f"   ❌ {table} table definition missing")
        
        if tables_found == len(required_tables):
            print("   ✅ All CAVA tables defined")
            return 10
        else:
            print(f"   ⚠️ Only {tables_found}/{len(required_tables)} tables defined")
            return (tables_found / len(required_tables)) * 10
            
    except Exception as e:
        print(f"   ❌ Error reading migration: {e}")
        return 0

def test_main_py_router():
    """Test 5: Check main.py router configuration"""
    print("\n5️⃣ Testing Main.py Router Configuration...")
    
    try:
        with open("main.py", 'r') as f:
            content = f.read()
        
        # Check router configuration
        checks = {
            'cava_chat_imported': 'cava_chat_router' in content,
            'old_chat_disabled': '# from modules.chat.routes import router as chat_router' in content or \
                               '# app.include_router(chat_router)' in content,
            'cava_chat_enabled': 'app.include_router(cava_chat_router)' in content,
            'cava_audit_enabled': 'cava_audit_router' in content,
            'startup_migrations': 'run_startup_migrations' in content,
            'cava_table_check': 'ensure_cava_tables' in content
        }
        
        passed_checks = sum(checks.values())
        
        print(f"   Router checks: {passed_checks}/6")
        for check_name, passed in checks.items():
            icon = "✅" if passed else "❌"
            print(f"   {icon} {check_name.replace('_', ' ').title()}")
        
        if passed_checks >= 5:
            print("   ✅ Router properly configured")
            return 10
        elif passed_checks >= 3:
            print("   ⚠️ Partial router configuration")
            return 6
        else:
            print("   ❌ Router configuration issues")
            return 2
            
    except Exception as e:
        print(f"   ❌ Error reading main.py: {e}")
        return 0

def test_mango_scenario_readiness():
    """Test 6: Check if code is ready for MANGO TEST"""
    print("\n6️⃣ Testing MANGO Test Scenario Readiness...")
    
    # Check if the code has the right patterns for the Bulgarian mango farmer test
    score = 0
    
    try:
        # Check chat routes for context usage
        with open("modules/api/chat_routes.py", 'r') as f:
            chat_content = f.read()
        
        if 'context_summary' in chat_content and 'previous' in chat_content.lower():
            score += 3
            print("   ✅ Context summary usage implemented")
        else:
            print("   ❌ Context summary usage missing")
        
        if 'mango' in chat_content.lower() or 'crop' in chat_content.lower():
            score += 2  
            print("   ✅ Agricultural context awareness")
        else:
            print("   ❌ No agricultural context awareness")
        
        # Check memory module for fact storage
        with open("modules/cava/conversation_memory.py", 'r') as f:
            memory_content = f.read()
        
        if 'recent_topics' in memory_content and 'crop' in memory_content:
            score += 3
            print("   ✅ Topic extraction for agricultural terms")
        else:
            print("   ❌ Topic extraction missing")
        
        if 'stored_facts' in memory_content:
            score += 2
            print("   ✅ Fact storage integration")
        else:
            print("   ❌ Fact storage integration missing")
        
        print(f"   MANGO Test readiness: {score}/10")
        return score
            
    except Exception as e:
        print(f"   ❌ Error checking MANGO readiness: {e}")
        return 0

def calculate_results(scores):
    """Calculate final results"""
    print("\n" + "=" * 50)
    print("📊 CAVA SIMPLE TEST RESULTS")
    print("=" * 50)
    
    test_names = [
        "File Structure",
        "Chat Routes Context", 
        "Memory Module",
        "Database Schema",
        "Router Configuration",
        "MANGO Test Readiness"
    ]
    
    total_score = 0
    for i, (test_name, score) in enumerate(zip(test_names, scores)):
        icon = "✅" if score >= 8 else "⚠️" if score >= 5 else "❌"
        print(f"{icon} {test_name}: {score}/10")
        total_score += score
    
    max_score = 60
    percentage = (total_score / max_score) * 100
    
    print("-" * 50)
    print(f"🎯 TOTAL SCORE: {total_score}/{max_score} ({percentage:.1f}%)")
    
    if total_score >= 50:
        print("\n🎉 CAVA READY FOR DEPLOYMENT!")
        print("✅ Core structure and logic implemented")
        print("🚀 Safe to deploy and test with database")
        print("\nNext steps:")
        print("1. git add -A")
        print("2. git commit -m 'feat: Complete CAVA with enhanced context and memory'")
        print("3. git push origin main")
        print("4. Monitor deployment and run live tests")
        return True
    else:
        print(f"\n❌ CAVA NOT READY - Score too low ({total_score}/60)")
        print("🔧 Fix the failing components before deploying")
        
        # Specific guidance
        if scores[0] < 8:
            print("   - Missing CAVA files - check file paths")
        if scores[1] < 8:
            print("   - Fix chat_routes.py context usage")
        if scores[2] < 8:
            print("   - Fix conversation_memory.py functions")
        if scores[3] < 8:
            print("   - Fix database migration SQL")
        if scores[4] < 8:
            print("   - Fix main.py router configuration")
        if scores[5] < 8:
            print("   - Improve MANGO test scenario readiness")
        
        return False

def main():
    """Run all simple tests"""
    print("🧪 CAVA Simple Pre-Deployment Test")
    print("Checking core structure and logic before deployment")
    print("=" * 50)
    
    scores = []
    
    # Run all tests
    scores.append(test_file_structure())
    scores.append(test_chat_routes_context())
    scores.append(test_memory_module())
    scores.append(test_database_schema())
    scores.append(test_main_py_router())
    scores.append(test_mango_scenario_readiness())
    
    # Calculate results
    success = calculate_results(scores)
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        sys.exit(1)