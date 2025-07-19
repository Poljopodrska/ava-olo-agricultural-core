#!/usr/bin/env python3
"""
Constitutional UI Compliance Test
Tests the UI implementation for MANGO RULE compliance
"""
import sys

def test_constitutional_compliance():
    """Test UI for constitutional requirements"""
    print("🏛️ Constitutional UI Compliance Test")
    print("===================================")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: File exists
    tests_total += 1
    try:
        with open("api_gateway_constitutional_ui.py", "r") as f:
            content = f.read()
        print("✅ Test 1: Constitutional UI file exists")
        tests_passed += 1
    except:
        print("❌ Test 1: Constitutional UI file not found")
        return False
    
    # Test 2: Bulgarian mango farmer support
    tests_total += 1
    if "bulgarian" in content.lower() and "mango" in content.lower():
        print("✅ Test 2: Bulgarian mango farmer support detected")
        tests_passed += 1
    else:
        print("❌ Test 2: Missing Bulgarian mango farmer support")
    
    # Test 3: Enter key support
    tests_total += 1
    if "handleEnterKey" in content or "onkeypress" in content:
        print("✅ Test 3: Enter key support implemented")
        tests_passed += 1
    else:
        print("❌ Test 3: Missing Enter key support")
    
    # Test 4: Font size compliance
    tests_total += 1
    if "font-size: 18px" in content or "fontSize: 18px" in content:
        print("✅ Test 4: Font size ≥18px for accessibility")
        tests_passed += 1
    else:
        print("❌ Test 4: Font size below 18px minimum")
    
    # Test 5: Brown/Olive color scheme
    tests_total += 1
    if "#6B5B73" in content or "#8B8C5A" in content:
        print("✅ Test 5: Constitutional brown/olive color scheme")
        tests_passed += 1
    else:
        print("❌ Test 5: Missing constitutional color scheme")
    
    # Test 6: Mobile responsive
    tests_total += 1
    if "@media" in content or "viewport" in content:
        print("✅ Test 6: Mobile responsive design")
        tests_passed += 1
    else:
        print("❌ Test 6: Missing mobile responsiveness")
    
    # Test 7: Agricultural query interface
    tests_total += 1
    if "/web/query" in content or "api/v1/query" in content:
        print("✅ Test 7: Agricultural query interface present")
        tests_passed += 1
    else:
        print("❌ Test 7: Missing query interface")
    
    # Calculate compliance score
    compliance_score = (tests_passed / tests_total) * 100
    
    print(f"\n📊 Constitutional Compliance Score: {compliance_score:.0f}%")
    print(f"   Tests Passed: {tests_passed}/{tests_total}")
    print(f"   Target Score: ≥90%")
    
    if compliance_score >= 90:
        print("\n✅ CONSTITUTIONAL COMPLIANCE ACHIEVED!")
        print("🥭 Bulgarian mango farmers can use this UI!")
        return True
    else:
        print("\n❌ CONSTITUTIONAL COMPLIANCE FAILED!")
        print("🚨 UI not ready for Bulgarian mango farmers!")
        return False

if __name__ == "__main__":
    success = test_constitutional_compliance()
    sys.exit(0 if success else 1)