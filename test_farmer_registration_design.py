#!/usr/bin/env python3
"""
Test farmer registration design and functionality
"""

import requests
import re
from datetime import datetime

def test_farmer_registration_design():
    """Test current farmer registration design issues"""
    
    print("🎨 FARMER REGISTRATION DESIGN ASSESSMENT")
    print("=" * 50)
    
    url = "https://6pmgrirjre.us-east-1.awsapprunner.com/farmer-registration"
    
    try:
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            content = response.text
            
            print("✅ Page accessible")
            
            # Check constitutional design elements
            design_checks = {
                "Constitutional Template": 'extends "base_constitutional.html"' in content,
                "Constitutional CSS": "constitutional-design.css" in content,
                "Brown/Olive Theme": any([
                    "--const-brown-primary" in content,
                    "--const-olive-primary" in content,
                    "constitutional-brown" in content
                ]),
                "Version Display": "current_version" in content,
                "Constitutional Buttons": "constitutional-submit-button" in content,
                "Add Field Button": "const-btn const-btn-primary" in content,
                "Form Sections": "constitutional-form-section" in content,
                "Mobile Responsive": "@media" in content,
                "18px+ Fonts": "--const-text-min" in content
            }
            
            print("\n📋 Constitutional Design Elements:")
            passed_checks = 0
            for check_name, passed in design_checks.items():
                status = "✅" if passed else "❌"
                print(f"  {status} {check_name}")
                if passed:
                    passed_checks += 1
            
            design_score = (passed_checks / len(design_checks)) * 100
            print(f"\n📊 Design Compliance Score: {design_score:.0f}%")
            
            # Check for functionality issues
            functionality_checks = {
                "Submit Button Present": '<button type="submit"' in content,
                "Form Action": 'onsubmit="submitFarmerRegistration' in content,
                "Field Addition": 'onclick="addFieldEntry' in content,
                "JavaScript Functions": "async function submitFarmerRegistration" in content,
                "Error/Success Messages": "error-message" in content and "success-message" in content
            }
            
            print("\n⚙️ Functionality Elements:")
            func_passed = 0
            for check_name, passed in functionality_checks.items():
                status = "✅" if passed else "❌"
                print(f"  {status} {check_name}")
                if passed:
                    func_passed += 1
            
            func_score = (func_passed / len(functionality_checks)) * 100
            print(f"\n📊 Functionality Score: {func_score:.0f}%")
            
            # Check for specific issues mentioned in spec
            issue_checks = {
                "Google Maps Error Check": "Something went wrong" not in content,
                "Field Size Manual Entry": "field_size_" in content,
                "Constitutional Colors": not any([
                    "green" in content.lower() and "button" in content.lower(),
                    "#00ff00" in content.lower(),
                    "rgb(0,255,0)" in content.lower()
                ])
            }
            
            print("\n🔍 Specific Issue Assessment:")
            for check_name, passed in issue_checks.items():
                status = "✅" if passed else "❌"
                print(f"  {status} {check_name}")
            
            # Overall assessment
            overall_score = (design_score + func_score) / 2
            print(f"\n📊 OVERALL ASSESSMENT: {overall_score:.0f}%")
            
            if overall_score >= 90:
                print("🎉 EXCELLENT: Registration design meets constitutional standards")
                return True
            elif overall_score >= 75:
                print("✅ GOOD: Minor improvements needed")
                return True
            else:
                print("❌ CRITICAL: Major design fixes required")
                return False
                
        else:
            print(f"❌ Page not accessible: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_farmer_registration_design()
    if success:
        print("\n✅ Farmer registration design assessment: PASSED")
    else:
        print("\n❌ Farmer registration design assessment: FAILED")
        print("🔧 Fixes required before MANGO compliance can be achieved")