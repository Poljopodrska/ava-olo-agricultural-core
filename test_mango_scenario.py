#!/usr/bin/env python3
"""
Test MANGO Scenario - Bulgarian farmer with session persistence
Simulates the exact scenario: farmer mentions mangoes, closes app, returns later
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"

def test_mango_scenario():
    """Test the complete MANGO scenario with session persistence"""
    print("🥭 MANGO TEST - Bulgarian Farmer Session Persistence")
    print("=" * 60)
    
    # Use a unique phone number for this test
    test_phone = f"+359887MANGO{datetime.now().strftime('%H%M')}"
    
    print(f"🇧🇬 Test farmer: {test_phone}")
    print(f"⏰ Starting time: {datetime.now().isoformat()}")
    print()
    
    # Session 1: Initial conversation about mangoes
    print("📱 SESSION 1: Farmer opens app, mentions mangoes")
    print("-" * 40)
    
    session1_messages = [
        "Hello, I am a farmer from Bulgaria",
        "I grow mangoes on my farm, about 3 hectares",
        "This is my first time growing mangoes in Bulgaria"
    ]
    
    for i, message in enumerate(session1_messages, 1):
        print(f"👨‍🌾 Message {i}: {message}")
        
        try:
            response = requests.post(f"{BASE_URL}/api/v1/chat", 
                                   json={
                                       "wa_phone_number": test_phone,
                                       "message": message
                                   }, timeout=60)
            
            if response.status_code == 200:
                chat_response = response.json()
                print(f"🤖 Response: {chat_response.get('response', '')[:100]}...")
                print(f"📊 Context: {chat_response.get('context_summary', '')[:100]}...")
                print()
            else:
                print(f"❌ Failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        time.sleep(1)  # Brief pause between messages
    
    print("📱 SESSION 1 COMPLETE - Farmer closes app")
    print("⏳ Simulating time gap (farmer returns later)...")
    print()
    
    # Wait a bit to simulate session gap
    time.sleep(5)
    
    # Session 2: Farmer returns and asks follow-up
    print("📱 SESSION 2: Farmer returns and asks follow-up")
    print("-" * 40)
    
    follow_up_message = "When should I harvest my mangoes?"
    
    print(f"👨‍🌾 Follow-up: {follow_up_message}")
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/chat", 
                               json={
                                   "wa_phone_number": test_phone,
                                   "message": follow_up_message
                               }, timeout=60)
        
        if response.status_code == 200:
            chat_response = response.json()
            response_text = chat_response.get('response', '')
            context_summary = chat_response.get('context_summary', '')
            
            print(f"🤖 Response: {response_text}")
            print()
            print(f"📊 Context Summary: {context_summary}")
            print()
            
            # Check memory indicators
            response_lower = response_text.lower()
            context_lower = context_summary.lower()
            
            memory_results = {
                "mentions_mangoes": "mango" in response_lower,
                "mentions_bulgaria": "bulgaria" in response_lower or "bulgaria" in context_lower,
                "mentions_hectares": "hectare" in response_lower or "3" in context_lower,
                "contextual_response": any(word in response_lower for word in ["your mango", "your farm", "previously", "mentioned"]),
                "returning_user_detected": "returning" in context_lower or "previous" in context_lower,
                "has_historical_context": len(context_summary) > 100
            }
            
            print("🧠 MEMORY TEST RESULTS:")
            print("-" * 25)
            
            score = 0
            for test_name, passed in memory_results.items():
                icon = "✅" if passed else "❌"
                print(f"{icon} {test_name.replace('_', ' ').title()}: {'PASS' if passed else 'FAIL'}")
                if passed:
                    score += 1
            
            print(f"\n🎯 Memory Score: {score}/6 ({(score/6)*100:.1f}%)")
            
            if score >= 4:
                print("🎉 MANGO TEST PASSED! Session persistence working!")
            elif score >= 2:
                print("⚠️ MANGO TEST PARTIAL - Some memory working")
            else:
                print("❌ MANGO TEST FAILED - Memory not persisting")
            
            print(f"\n📈 Expected Audit Improvement:")
            print(f"   Session Persistence: Should improve from 0/10")
            print(f"   Memory System: Should improve from 5/10")
            print(f"   Overall Score: Should improve from 45/60")
            
        else:
            print(f"❌ Follow-up failed: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Follow-up error: {e}")

def check_audit_improvement():
    """Check if the audit score improved after the test"""
    print("\n" + "=" * 60)
    print("📊 CHECKING AUDIT SCORE IMPROVEMENT")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/cava/audit", timeout=30)
        if response.status_code == 200:
            audit_data = response.json()
            
            print(f"🎯 Current Score: {audit_data['score']}/60 ({audit_data['percentage']:.1f}%)")
            print()
            
            components = audit_data['components']
            for component_name, component_data in components.items():
                status_icon = "✅" if component_data['status'] == 'PASS' else "⚠️" if component_data['status'] == 'PARTIAL' else "❌"
                print(f"{status_icon} {component_name.replace('_', ' ').title()}: {component_data['score']}/10 ({component_data['status']})")
            
            # Check for specific improvements
            session_score = components.get('session_persistence', {}).get('score', 0)
            memory_score = components.get('memory_system', {}).get('score', 0)
            
            print(f"\n🎯 Key Metrics:")
            print(f"   Session Persistence: {session_score}/10")
            print(f"   Memory System: {memory_score}/10")
            
            if session_score > 0:
                print("✅ Session persistence improvement detected!")
            if memory_score >= 8:
                print("✅ Memory system working well!")
            
            if audit_data['score'] >= 50:
                print(f"\n🎉 SUCCESS! CAVA score reached {audit_data['score']}/60 (target: 50+)")
            else:
                print(f"\n⚠️ Still working: {audit_data['score']}/60 (target: 50+)")
                
        else:
            print(f"❌ Audit check failed: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Audit check error: {e}")

if __name__ == "__main__":
    test_mango_scenario()
    check_audit_improvement()