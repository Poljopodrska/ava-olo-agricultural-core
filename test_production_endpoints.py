#!/usr/bin/env python3
"""
Production Endpoint Tester
Test the CAVA debug endpoints after deployment to identify the AWS issue
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"

def test_debug_endpoints():
    """Test all debug endpoints to identify the issue"""
    print("🔍 CAVA Production Diagnostics")
    print("=" * 50)
    print(f"Testing: {BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    print()
    
    # Test 1: Check all chat endpoints
    print("1️⃣ Checking all chat endpoints...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/cava/debug/endpoints", timeout=30)
        if response.status_code == 200:
            data = response.json()['data']
            print(f"   ✅ Found {len(data['chat_routes'])} chat routes:")
            for route in data['chat_routes']:
                print(f"      - {route['path']} → {route['module']}")
            
            if data.get('critical_issue'):
                print(f"   🚨 CRITICAL: {data['critical_issue']}")
        else:
            print(f"   ❌ Failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Which chat endpoint is active
    print("\n2️⃣ Identifying active chat endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/cava/debug/which-chat-active", timeout=30)
        if response.status_code == 200:
            data = response.json()['data']
            print(f"   📍 Primary endpoint: {data.get('primary_chat_endpoint', 'Not found')}")
            
            for path, info in data['chat_endpoints'].items():
                has_cava = "✅" if info.get('has_cava') else "❌"
                size = info.get('source_size', 0)
                print(f"   {has_cava} {path}: {size} chars, CAVA: {info.get('has_cava', False)}")
                
            if data.get('likely_issue'):
                print(f"   ⚠️ Issue: {data['likely_issue']}")
        else:
            print(f"   ❌ Failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Trace execution
    print("\n3️⃣ Tracing chat execution...")
    try:
        response = requests.post(f"{BASE_URL}/api/v1/cava/debug/trace-chat", timeout=30)
        if response.status_code == 200:
            data = response.json()['data']
            
            print(f"   Steps completed:")
            for step in data.get('steps', []):
                print(f"      {step}")
            
            print(f"   Errors:")
            for error in data.get('errors', []):
                print(f"      {error}")
            
            print(f"   🧠 Context found: {data.get('context_found', False)}")
            print(f"   🤖 CAVA active: {data.get('cava_active', False)}")
            print(f"   📝 Has CAVA code: {data.get('has_cava_code', False)}")
            
            if data.get('cava_patterns_found'):
                patterns = data['cava_patterns_found']
                found_count = sum(patterns.values())
                print(f"   🎯 CAVA patterns: {found_count}/5 found")
                for pattern, found in patterns.items():
                    icon = "✅" if found else "❌"
                    print(f"      {icon} {pattern}")
        else:
            print(f"   ❌ Failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Memory flow
    print("\n4️⃣ Testing memory flow...")
    try:
        response = requests.post(f"{BASE_URL}/api/v1/cava/debug/test-memory-flow", timeout=60)
        if response.status_code == 200:
            data = response.json()['data']
            
            memory_test = data.get('memory_test', {})
            print(f"   📊 Memory test results:")
            print(f"      Messages stored: {'✅' if memory_test.get('all_messages_stored') else '❌'}")
            print(f"      Context complete: {'✅' if memory_test.get('context_complete') else '❌'}")
            print(f"      Remembers facts: {'✅' if memory_test.get('remembers_key_facts') else '❌'}")
            print(f"      Memory working: {'✅' if memory_test.get('memory_working') else '❌'}")
            
            print(f"   📝 Context: {data.get('final_context_summary', 'None')[:100]}...")
            print(f"   🔬 Diagnosis: {data.get('diagnosis', 'Unknown')}")
        else:
            print(f"   ❌ Failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 5: AWS vs Local comparison
    print("\n5️⃣ AWS vs Local comparison...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/cava/debug/aws-vs-local", timeout=30)
        if response.status_code == 200:
            data = response.json()['data']
            
            env = data['comparison']['environment']
            print(f"   🏗️ Environment:")
            print(f"      Container: {'✅' if env.get('is_container') else '❌'}")
            print(f"      OpenAI key: {'✅' if env.get('has_openai_key') else '❌'}")
            print(f"      Python: {env.get('python_version', 'unknown')}")
            
            modules = data['comparison']['modules']
            print(f"   📦 Critical modules:")
            for module, info in modules.items():
                if 'cava' in module or 'chat' in module:
                    status = "✅" if info.get('loaded') else "❌"
                    print(f"      {status} {module}")
            
            db = data['comparison']['database']
            print(f"   💾 Database:")
            print(f"      Connected: {'✅' if db.get('connected') else '❌'}")
            print(f"      CAVA tables: {len(db.get('cava_tables', []))}/3")
            
            issues = [issue for issue in data.get('likely_issues', []) if issue]
            if issues:
                print(f"   ⚠️ Likely issues:")
                for issue in issues:
                    print(f"      - {issue}")
        else:
            print(f"   ❌ Failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 DIAGNOSIS COMPLETE")
    print("\nNext steps based on findings:")
    print("1. If multiple chat endpoints found → Router conflict")
    print("2. If CAVA code missing → Module loading issue")
    print("3. If memory works but chat doesn't use it → Endpoint routing issue")
    print("4. If modules not loaded → Import order problem")
    print("\nTo fix:")
    print("- Try /api/v1/cava/debug/force-fix for emergency patch")
    print("- Or restart ECS service for clean deployment")

def test_actual_chat_endpoint():
    """Test the actual chat endpoint that the UI uses"""
    print("\n" + "=" * 50)
    print("🧪 Testing Actual Chat Endpoint")
    print("=" * 50)
    
    test_phone = "+385991234TEST"
    test_message = "I grow mangoes in Bulgaria and need harvest advice"
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/chat", 
                               json={
                                   "wa_phone_number": test_phone,
                                   "message": test_message
                               }, timeout=60)
        
        if response.status_code == 200:
            chat_response = response.json()
            
            print(f"✅ Chat endpoint working")
            print(f"   Response: {chat_response.get('response', '')[:150]}...")
            print(f"   Model: {chat_response.get('model_used', 'unknown')}")
            
            # Check for memory indicators
            response_text = chat_response.get('response', '').lower()
            has_context = chat_response.get('context_used', False)
            context_summary = chat_response.get('context_summary', '')
            
            print(f"   Context used: {'✅' if has_context else '❌'}")
            print(f"   Context summary: {context_summary[:100]}...")
            
            # Test follow-up for memory
            follow_up_response = requests.post(f"{BASE_URL}/api/v1/chat",
                                             json={
                                                 "wa_phone_number": test_phone,
                                                 "message": "When should I harvest?"
                                             }, timeout=60)
            
            if follow_up_response.status_code == 200:
                follow_data = follow_up_response.json()
                follow_text = follow_data.get('response', '').lower()
                
                remembers_mangoes = 'mango' in follow_text
                print(f"   Memory test: {'✅' if remembers_mangoes else '❌'} (mentions mangoes: {remembers_mangoes})")
                print(f"   Follow-up: {follow_data.get('response', '')[:100]}...")
                
                if not remembers_mangoes:
                    print(f"   🚨 MEMORY ISSUE: Chat doesn't remember mangoes!")
            
        else:
            print(f"❌ Chat endpoint failed: HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Chat test error: {e}")

if __name__ == "__main__":
    test_debug_endpoints()
    test_actual_chat_endpoint()