#!/usr/bin/env python3
"""
Quick CAVA Integration Test
Tests if the chat endpoint is now properly using CAVA after fixing the router conflict
"""
import requests
import json
import time

BASE_URL = "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"

def test_cava_integration():
    print("🧪 Testing CAVA Integration After Router Fix")
    print("=" * 50)
    
    # Test 1: Check if debug endpoint works
    print("\n1️⃣ Testing Chat Debug Endpoint")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/chat/debug", timeout=30)
        if response.status_code == 200:
            debug_info = response.json()
            print(f"✅ Debug endpoint accessible")
            print(f"   CAVA Memory: {'✅' if debug_info.get('cava_memory_initialized') else '❌'}")
            print(f"   Database: {'✅' if debug_info.get('database_connected') else '❌'}")
            print(f"   Chat Table: {'✅' if debug_info.get('chat_messages_table_exists') else '❌'}")
            print(f"   OpenAI Client: {'✅' if debug_info.get('openai_client_available') else '❌'}")
            print(f"   Integration Active: {'✅' if debug_info.get('cava_integration_active') else '❌'}")
        else:
            print(f"❌ Debug endpoint failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Debug endpoint error: {e}")
    
    # Test 2: Test direct CAVA functionality
    print("\n2️⃣ Testing Direct CAVA Functionality")
    try:
        response = requests.post(f"{BASE_URL}/api/v1/chat/test-cava-direct", timeout=30)
        if response.status_code == 200:
            cava_test = response.json()
            print(f"✅ Direct CAVA test accessible")
            print(f"   Status: {cava_test.get('status')}")
            print(f"   Message Stored: {'✅' if cava_test.get('message_stored') else '❌'}")
            print(f"   Storage Count: {cava_test.get('storage_count', 0)}")
            print(f"   Context Retrieved: {'✅' if cava_test.get('context_retrieved') else '❌'}")
            print(f"   CAVA Working: {'✅' if cava_test.get('cava_working_directly') else '❌'}")
        else:
            print(f"❌ Direct CAVA test failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Direct CAVA test error: {e}")
    
    # Test 3: Test actual chat endpoint with CAVA
    print("\n3️⃣ Testing Chat Endpoint with CAVA")
    test_phone = "+359887123456"  # Bulgarian test number
    test_message = "I grow mangoes in Bulgaria and need help"
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/chat", 
                               json={
                                   "wa_phone_number": test_phone,
                                   "message": test_message
                               }, timeout=60)
        
        if response.status_code == 200:
            chat_response = response.json()
            print(f"✅ Chat endpoint working")
            print(f"   Response: {chat_response.get('response', '')[:100]}...")
            print(f"   Model: {chat_response.get('model_used', 'unknown')}")
            print(f"   Facts: {chat_response.get('facts_extracted', 'none')}")
            
            # Wait a moment then test memory
            time.sleep(2)
            
            # Follow-up message to test memory
            follow_up = "What should I do for harvest time?"
            response2 = requests.post(f"{BASE_URL}/api/v1/chat",
                                    json={
                                        "wa_phone_number": test_phone,
                                        "message": follow_up
                                    }, timeout=60)
            
            if response2.status_code == 200:
                follow_response = response2.json()
                response_text = follow_response.get('response', '').lower()
                
                # Check if it remembers mangoes
                memory_indicators = {
                    'mentions_mango': 'mango' in response_text,
                    'mentions_harvest': 'harvest' in response_text,
                    'contextual': any(word in response_text for word in ['your mango', 'your crop', 'your fruit'])
                }
                
                print(f"\n🧠 Memory Test Results:")
                for indicator, detected in memory_indicators.items():
                    icon = "✅" if detected else "❌"
                    print(f"   {icon} {indicator}: {'YES' if detected else 'NO'}")
                
                memory_score = sum(memory_indicators.values())
                print(f"\n📊 Memory Score: {memory_score}/3")
                
                if memory_score >= 2:
                    print(f"🎉 MEMORY TEST PASSED! CAVA is working!")
                else:
                    print(f"⚠️  Memory test shows limited functionality")
                    
        else:
            print(f"❌ Chat endpoint failed: HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Chat endpoint error: {e}")
    
    # Test 4: Check database storage
    print("\n4️⃣ Checking Database Storage")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/cava/table-status", timeout=30)
        if response.status_code == 200:
            table_status = response.json()
            
            for table, status in table_status.get('tables', {}).items():
                icon = "✅" if status.get('exists') else "❌"
                count = status.get('row_count', 0)
                print(f"   {icon} {table}: {count} rows")
            
            print(f"\n🎯 CAVA Ready: {'✅' if table_status.get('cava_ready') else '❌'}")
            
    except Exception as e:
        print(f"❌ Table status error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 CAVA Integration Test Complete!")
    print("\nExpected Results After Fix:")
    print("✅ Debug endpoint should show CAVA integration active")
    print("✅ Direct CAVA test should work")
    print("✅ Chat endpoint should use CAVA and show memory")
    print("✅ Messages should be stored in database")

if __name__ == "__main__":
    test_cava_integration()