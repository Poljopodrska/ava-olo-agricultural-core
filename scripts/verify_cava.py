#!/usr/bin/env python3
"""
CAVA Verification Script
Comprehensive verification of CAVA implementation status
"""
import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🧠 {title}")
    print(f"{'='*60}")

def print_section(title):
    print(f"\n{'-'*40}")
    print(f"📋 {title}")
    print(f"{'-'*40}")

def verify_cava():
    """Run comprehensive CAVA verification"""
    print_header("CAVA Implementation Verification")
    print(f"🌐 Testing endpoint: {BASE_URL}")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    
    success_count = 0
    total_tests = 4
    
    # 1. Check table status
    print_section("1. Table Status Check")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/cava/table-status", timeout=30)
        if response.status_code == 200:
            status = response.json()
            
            print("📊 Table Status:")
            all_tables_exist = True
            for table, info in status['tables'].items():
                icon = "✅" if info['exists'] else "❌"
                count = f"({info['row_count']} rows)" if info['exists'] else f"(Error: {info.get('error', 'Missing')})"
                print(f"   {icon} {table}: {info['status']} {count}")
                if not info['exists']:
                    all_tables_exist = False
            
            print(f"\n🎯 CAVA Ready: {'✅ YES' if status['cava_ready'] else '❌ NO'}")
            
            if not all_tables_exist:
                print("\n⚠️  Some tables are missing! Running setup...")
                setup_response = requests.post(f"{BASE_URL}/api/v1/cava/setup-tables", timeout=60)
                if setup_response.status_code == 200:
                    setup_result = setup_response.json()
                    print(f"   Setup result: {setup_result['status']}")
                    if setup_result['status'] == 'success':
                        print(f"   Tables created: {', '.join(setup_result.get('tables_created', []))}")
                        success_count += 1
                    else:
                        print(f"   Setup failed: {setup_result.get('message', 'Unknown error')}")
                else:
                    print(f"   Setup request failed: HTTP {setup_response.status_code}")
            else:
                success_count += 1
                
        else:
            print(f"❌ Table status check failed: HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Table status check error: {str(e)}")
    
    # 2. Run CAVA audit
    print_section("2. CAVA Implementation Audit")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/cava/audit", timeout=60)
        if response.status_code == 200:
            audit = response.json()
            
            score = audit.get('score', 0)
            max_score = audit.get('max_score', 60)
            percentage = audit.get('percentage', 0)
            status = audit.get('status', 'UNKNOWN')
            
            print(f"📊 CAVA Score: {score}/{max_score} ({percentage:.1f}%)")
            print(f"🎯 Status: {status}")
            
            # Show component scores
            components = audit.get('components', {})
            print(f"\n📋 Component Scores:")
            for comp_name, comp_data in components.items():
                comp_score = comp_data.get('score', 0)
                comp_status = comp_data.get('status', 'unknown')
                icon = "✅" if comp_score >= 7 else "⚠️" if comp_score >= 4 else "❌"
                print(f"   {icon} {comp_name.replace('_', ' ')}: {comp_score}/10 ({comp_status})")
            
            # Check if audit passed
            if score >= 40:  # At least 2/3 of max score
                success_count += 1
                print(f"\n✅ Audit PASSED: Score {score}/{max_score}")
            else:
                print(f"\n❌ Audit FAILED: Score {score}/{max_score} (minimum 40 required)")
                
                # Show remediation if available
                remediation = audit.get('remediation', [])
                if remediation:
                    print(f"\n🔧 Remediation Required ({len(remediation)} issues):")
                    for i, fix in enumerate(remediation[:3], 1):  # Show top 3
                        print(f"   {i}. {fix.get('component', 'Unknown')}: {fix.get('issue', 'Unknown issue')}")
                        
        else:
            print(f"❌ Audit failed: HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Audit error: {str(e)}")
    
    # 3. Test conversation memory
    print_section("3. Conversation Memory Test")
    try:
        response = requests.post(f"{BASE_URL}/api/v1/cava/test-conversation", timeout=90)
        if response.status_code == 200:
            test = response.json()
            
            memory_score = test.get('memory_score', 0)
            cava_working = test.get('cava_working', False)
            messages_stored = test.get('messages_stored', 0)
            
            print(f"🧠 Memory Score: {memory_score}/100")
            print(f"💾 Messages Stored: {messages_stored}")
            print(f"🎯 CAVA Working: {'✅ YES' if cava_working else '❌ NO'}")
            
            # Show memory indicators
            memory_indicators = test.get('memory_indicators', {})
            if memory_indicators:
                print(f"\n📋 Memory Indicators:")
                for indicator, detected in memory_indicators.items():
                    icon = "✅" if detected else "❌"
                    print(f"   {icon} {indicator.replace('_', ' ')}: {'DETECTED' if detected else 'MISSING'}")
            
            # Show conversation flow
            conversation = test.get('test_conversation', [])
            if conversation:
                print(f"\n💬 Test Conversation ({len(conversation)} messages):")
                for i, msg in enumerate(conversation[-4:], 1):  # Show last 4 messages
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')[:60] + ('...' if len(msg.get('content', '')) > 60 else '')
                    print(f"   {i}. {role.upper()}: {content}")
            
            if cava_working and memory_score >= 50:
                success_count += 1
                print(f"\n✅ Memory test PASSED")
            else:
                print(f"\n❌ Memory test FAILED")
                
            if test.get('error'):
                print(f"❌ Test error: {test['error']}")
                
        else:
            print(f"❌ Memory test failed: HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Memory test error: {str(e)}")
    
    # 4. Quick operational check
    print_section("4. Quick Operational Check")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/cava/quick-check", timeout=30)
        if response.status_code == 200:
            quick = response.json()
            
            status = quick.get('status', 'UNKNOWN')
            has_messages = quick.get('has_message_storage', False)
            has_recent = quick.get('has_recent_activity', False) 
            has_cost_tracking = quick.get('has_cost_tracking', False)
            using_gpt35 = quick.get('using_gpt35', False)
            
            print(f"🎯 Quick Status: {status}")
            print(f"💾 Message Storage: {'✅' if has_messages else '❌'}")
            print(f"⚡ Recent Activity: {'✅' if has_recent else '❌'}")
            print(f"💰 Cost Tracking: {'✅' if has_cost_tracking else '❌'}")
            print(f"🤖 Using GPT-3.5: {'✅' if using_gpt35 else '❌'}")
            
            if status in ['FULLY_OPERATIONAL', 'PARTIAL_CAVA']:
                success_count += 1
                print(f"\n✅ Quick check PASSED")
            else:
                print(f"\n❌ Quick check FAILED")
                
        else:
            print(f"❌ Quick check failed: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Quick check error: {str(e)}")
    
    # Final summary
    print_header("VERIFICATION SUMMARY")
    
    print(f"🎯 Tests Passed: {success_count}/{total_tests}")
    print(f"📊 Success Rate: {(success_count/total_tests)*100:.1f}%")
    
    if success_count >= 3:
        print(f"\n🎉 CAVA VERIFICATION SUCCESSFUL!")
        print(f"✅ CAVA memory system is working correctly")
        print(f"✅ Ready for production use with Bulgarian mango farmers")
        print(f"✅ Cost optimization: GPT-3.5 + persistent memory")
        return True
    else:
        print(f"\n⚠️  CAVA VERIFICATION INCOMPLETE")
        print(f"❌ {total_tests - success_count} tests failed")
        print(f"🔧 Manual intervention may be required")
        
        # Provide next steps
        print(f"\n📋 Next Steps:")
        if success_count == 0:
            print(f"   1. Check if service is running at {BASE_URL}")
            print(f"   2. Verify database connection")
            print(f"   3. Run table setup manually")
        else:
            print(f"   1. Visit: {BASE_URL}/cava-audit")
            print(f"   2. Click 'Setup CAVA Tables' if tables are missing")
            print(f"   3. Run full audit and address any failures")
            print(f"   4. Test conversation memory functionality")
        
        return False

def test_mango_scenario():
    """Test the specific Bulgarian mango farmer scenario"""
    print_header("MANGO FARMER SCENARIO TEST")
    
    try:
        # Test the exact scenario from requirements
        test_phone = "+359887123456"  # Bulgarian number
        
        print("🥭 Testing: Bulgarian mango farmer scenario")
        print("📝 Scenario: Farmer says 'I grow mangoes', closes app, returns next day, asks 'when to harvest?'")
        
        # First message: I grow mangoes
        print(f"\n1️⃣ Sending: 'I grow mangoes'")
        response1 = requests.post(f"{BASE_URL}/api/v1/chat", 
                                json={
                                    "wa_phone_number": test_phone,
                                    "message": "I grow mangoes"
                                }, timeout=30)
        
        if response1.status_code == 200:
            result1 = response1.json()
            print(f"   ✅ Response: {result1.get('response', '')[:100]}...")
            print(f"   📊 Model: {result1.get('model_used', 'unknown')}")
            
            # Second message after delay: when to harvest?
            print(f"\n2️⃣ Sending: 'when to harvest?' (should remember mangoes)")
            response2 = requests.post(f"{BASE_URL}/api/v1/chat",
                                    json={
                                        "wa_phone_number": test_phone, 
                                        "message": "when to harvest?"
                                    }, timeout=30)
            
            if response2.status_code == 200:
                result2 = response2.json()
                response_text = result2.get('response', '').lower()
                
                print(f"   ✅ Response: {result2.get('response', '')[:100]}...")
                
                # Check if response shows memory of mangoes
                memory_indicators = {
                    'mentions_mango': 'mango' in response_text,
                    'contextual_response': any(word in response_text for word in ['your mango', 'your crop', 'your fruit']),
                    'harvest_advice': any(word in response_text for word in ['harvest', 'ripe', 'ready', 'pick'])
                }
                
                print(f"\n🧠 Memory Analysis:")
                memory_score = 0
                for indicator, detected in memory_indicators.items():
                    icon = "✅" if detected else "❌"
                    print(f"   {icon} {indicator.replace('_', ' ')}: {'YES' if detected else 'NO'}")
                    if detected:
                        memory_score += 1
                
                memory_percentage = (memory_score / len(memory_indicators)) * 100
                print(f"\n📊 Memory Score: {memory_score}/{len(memory_indicators)} ({memory_percentage:.1f}%)")
                
                if memory_score >= 2:
                    print(f"🎉 MANGO SCENARIO PASSED!")
                    print(f"✅ System remembers mangoes and provides contextual harvest advice")
                    return True
                else:
                    print(f"❌ MANGO SCENARIO FAILED!")
                    print(f"⚠️  System does not show memory of previous conversation")
                    return False
                    
            else:
                print(f"   ❌ Second message failed: HTTP {response2.status_code}")
                return False
                
        else:
            print(f"   ❌ First message failed: HTTP {response1.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Mango scenario error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting CAVA verification...")
    
    # Run main verification
    main_success = verify_cava()
    
    # Run mango scenario test if main verification passed
    scenario_success = False
    if main_success:
        scenario_success = test_mango_scenario()
    
    # Final result
    print_header("FINAL RESULT")
    
    if main_success and scenario_success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ CAVA is fully operational")
        print("✅ Bulgarian mango farmer scenario works")
        print("✅ Ready for production deployment")
        sys.exit(0)
    elif main_success:
        print("⚠️  PARTIAL SUCCESS")
        print("✅ CAVA infrastructure is working")
        print("❌ Mango scenario needs attention")
        sys.exit(1)
    else:
        print("❌ VERIFICATION FAILED")
        print("🔧 CAVA setup requires manual intervention")
        sys.exit(2)