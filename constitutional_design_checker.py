#!/usr/bin/env python3
"""
Constitutional Design Compliance Checker
Verifies all design requirements are met
"""

import os
import re
import requests

def check_css_compliance():
    """Check CSS file for constitutional compliance"""
    
    print("🎨 Checking Constitutional CSS Compliance")
    print("-" * 40)
    
    css_file = "static/css/constitutional-design.css"
    
    if not os.path.exists(css_file):
        print("❌ Constitutional CSS file not found")
        return False
    
    with open(css_file, 'r') as f:
        css_content = f.read()
    
    # Check for required elements
    checks = {
        "Brown/Olive Colors": any([
            "#8B6F47" in css_content,  # Brown
            "#6B8E23" in css_content,  # Olive
            "--const-brown-primary" in css_content,
            "--const-olive-primary" in css_content
        ]),
        "Minimum 18px Font": "--const-text-min: 18px" in css_content,
        "MANGO Rule Reference": "mango" in css_content.lower(),
        "Bulgarian Compliance": "bulgarian" in css_content.lower(),
        "Farmer Accessibility": any([
            "farmer" in css_content.lower(),
            "accessibility" in css_content.lower(),
            "--const-spacing" in css_content
        ]),
        "Constitutional Variables": all([
            "--const-" in css_content,
            "constitutional" in css_content.lower()
        ])
    }
    
    total_checks = len(checks)
    passed_checks = sum(checks.values())
    compliance_score = (passed_checks / total_checks) * 100
    
    print(f"CSS Compliance Score: {compliance_score:.1f}%")
    
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")
    
    return compliance_score >= 80

def check_template_compliance():
    """Check templates for constitutional compliance"""
    
    print("\n🏛️ Checking Template Compliance")
    print("-" * 40)
    
    template_files = [
        "templates/base_constitutional.html",
        "templates/ui_dashboard_enhanced.html",
        "templates/register_fields.html",
        "templates/farmer_registration.html"
    ]
    
    compliance_issues = []
    total_templates = len(template_files)
    compliant_templates = 0
    
    for template_file in template_files:
        if not os.path.exists(template_file):
            compliance_issues.append(f"Missing: {template_file}")
            continue
            
        with open(template_file, 'r') as f:
            template_content = f.read()
        
        # Check for constitutional elements
        template_checks = {
            "Constitutional CSS": "constitutional-design.css" in template_content,
            "Constitutional Classes": "const-" in template_content,
            "Minimum Text Size": any([
                "var(--const-text-" in template_content,
                "font-size: 18px" in template_content,
                "font-size: 20px" in template_content
            ]),
            "Brown/Olive Theme": any([
                "const-brown" in template_content,
                "const-olive" in template_content
            ])
        }
        
        template_score = sum(template_checks.values()) / len(template_checks) * 100
        
        if template_score >= 75:
            compliant_templates += 1
            print(f"  ✅ {os.path.basename(template_file)}: {template_score:.0f}%")
        else:
            print(f"  ❌ {os.path.basename(template_file)}: {template_score:.0f}%")
            for check_name, passed in template_checks.items():
                if not passed:
                    compliance_issues.append(f"{template_file}: Missing {check_name}")
    
    template_compliance = (compliant_templates / total_templates) * 100
    print(f"Template Compliance: {compliant_templates}/{total_templates} ({template_compliance:.0f}%)")
    
    return template_compliance >= 75, compliance_issues

def check_production_compliance():
    """Check production deployment for compliance"""
    
    print("\n🌐 Checking Production Compliance")
    print("-" * 40)
    
    url = "https://6pmgrirjre.us-east-1.awsapprunner.com"
    
    try:
        # Check CSS is accessible
        css_response = requests.get(f"{url}/static/css/constitutional-design.css", timeout=10)
        css_accessible = css_response.status_code == 200
        
        # Check main page
        main_response = requests.get(f"{url}/", timeout=10)
        main_accessible = main_response.status_code == 200
        
        production_checks = {
            "CSS Accessible": css_accessible,
            "Main Page Accessible": main_accessible,
            "Constitutional Design": css_accessible and "const-" in css_response.text if css_accessible else False,
            "Agricultural Theme": main_accessible and "agricultural" in main_response.text.lower() if main_accessible else False
        }
        
        production_score = sum(production_checks.values()) / len(production_checks) * 100
        
        print(f"Production Compliance: {production_score:.0f}%")
        
        for check_name, passed in production_checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}")
            
        return production_score >= 75
        
    except Exception as e:
        print(f"❌ Production check failed: {str(e)}")
        return False

def generate_compliance_report():
    """Generate comprehensive compliance report"""
    
    print("\n" + "="*50)
    print("🏛️ CONSTITUTIONAL DESIGN COMPLIANCE REPORT")
    print("="*50)
    
    css_compliant = check_css_compliance()
    template_compliant, issues = check_template_compliance()
    production_compliant = check_production_compliance()
    
    overall_compliance = [css_compliant, template_compliant, production_compliant]
    compliance_score = sum(overall_compliance) / len(overall_compliance) * 100
    
    print(f"\n📊 OVERALL COMPLIANCE SCORE: {compliance_score:.0f}%")
    
    if compliance_score >= 95:
        print("🎉 EXCELLENT: Constitutional compliance achieved!")
        print("🥭 Bulgarian Mango Farmer Approved")
    elif compliance_score >= 80:
        print("✅ GOOD: Constitutional compliance acceptable")
        print("🔧 Minor improvements recommended")
    else:
        print("❌ NEEDS WORK: Constitutional compliance insufficient")
        print("🚨 Immediate fixes required")
    
    if issues:
        print("\n🔧 Issues to Address:")
        for issue in issues[:10]:  # Show top 10 issues
            print(f"  - {issue}")
    
    print(f"\n🏛️ Constitutional Principles Status:")
    print(f"  Principle #14 (Design-First): {'✅' if compliance_score >= 80 else '❌'}")
    print(f"  MANGO Rule Compliance: {'✅' if css_compliant else '❌'}")
    print(f"  Farmer Accessibility: {'✅' if template_compliant else '❌'}")
    
    return compliance_score >= 95

if __name__ == "__main__":
    success = generate_compliance_report()
    exit(0 if success else 1)