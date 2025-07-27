#!/usr/bin/env python3
"""
Test script to verify CAVA chat integration with GPT-3.5
Tests the exact endpoints that the dashboard uses
"""
import requests
import json

BASE_URL = "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"
#BASE_URL = "http://localhost:8080"  # Use for local testing

def test_chat_status():
    """Test the chat status endpoint that dashboard uses"""
    print("🔍 Testing Chat Status Endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/chat/status")
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Connected: {data.get('connected', False)}")
        print(f"Has API Key: {data.get('has_api_key', False)}")
        print(f"OpenAI Status: {data.get('openai_status', 'Unknown')}")
        
        if data.get('connected') and data.get('has_api_key'):
            print("✅ Status check PASSED - Should show 'Connected to GPT-3.5'")
            return True
        else:
            print("❌ Status check FAILED - Will show 'Chat AI is not connected'")
            return False
            
    except Exception as e:
        print(f"❌ Status check ERROR: {e}")
        return False

def test_chat_message():
    """Test the chat message endpoint that dashboard uses"""
    print("\n🔍 Testing Chat Message Endpoint...")
    
    test_message = "What fertilizer should I use for tomatoes?"
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/chat/message",
            headers={"Content-Type": "application/json"},
            json={"content": test_message}
        )
        
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Success: {data.get('success', False)}")
        print(f"AI Connected: {data.get('ai_connected', False)}")
        print(f"Model: {data.get('model', 'Unknown')}")
        print(f"Tokens Used: {data.get('tokens_used', 0)}")
        print(f"Response: {data.get('response', 'No response')[:200]}...")
        
        if data.get('success') and data.get('ai_connected'):
            print("✅ Chat message PASSED - GPT-3.5 responding")
            return True
        else:
            print("❌ Chat message FAILED - Using fallback")
            return False
            
    except Exception as e:
        print(f"❌ Chat message ERROR: {e}")
        return False

def test_cava_engine_direct():
    """Test the CAVA engine endpoint directly"""
    print("\n🔍 Testing CAVA Engine Direct...")
    
    test_message = "How do I grow mangoes in Slovenia?"
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/chat/cava-engine",
            headers={"Content-Type": "application/json"},
            json={
                "wa_phone_number": "+385991234567",
                "message": test_message
            }
        )
        
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Model Used: {data.get('model_used', 'Unknown')}")
        print(f"Context Used: {data.get('context_used', False)}")
        print(f"Response Length: {len(data.get('response', ''))}")
        print(f"Response Preview: {data.get('response', 'No response')[:200]}...")
        
        if data.get('model_used') == 'gpt-3.5-turbo':
            print("✅ CAVA Engine PASSED - Using GPT-3.5")
            return True
        else:
            print("❌ CAVA Engine FAILED - Not using GPT-3.5")
            return False
            
    except Exception as e:
        print(f"❌ CAVA Engine ERROR: {e}")
        return False

def test_openai_debug():
    """Test the OpenAI debug endpoint"""
    print("\n🔍 Testing OpenAI Debug...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/cava/debug/openai-connection")
        data = response.json()
        
        connection_status = data.get('connection_test', {}).get('status', 'unknown')
        print(f"Connection Status: {connection_status}")
        
        if connection_status == 'success':
            print("✅ OpenAI Debug PASSED - Connection successful")
            return True
        else:
            print("❌ OpenAI Debug FAILED - Connection issues")
            return False
            
    except Exception as e:
        print(f"❌ OpenAI Debug ERROR: {e}")
        return False

def main():
    """Run all tests and report results"""
    print("🧪 CAVA Chat Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Chat Status", test_chat_status),
        ("Chat Message", test_chat_message),
        ("CAVA Engine", test_cava_engine_direct),
        ("OpenAI Debug", test_openai_debug)
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("TEST RESULTS:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 SUCCESS: CAVA chat is fully integrated with GPT-3.5!")
        print("Dashboard should now show 'Connected to GPT-3.5' instead of error message.")
    else:
        print(f"\n⚠️ ISSUES: {len(tests) - passed} tests failed - chat integration needs work")
    
    return passed == len(tests)

if __name__ == "__main__":
    main()