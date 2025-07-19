#!/usr/bin/env python3
"""
Design Consistency Verification with Agricultural Core Service
Verifies all design elements match constitutional requirements
"""

import os
import re
import json
from pathlib import Path

def analyze_css_compliance():
    """Analyze CSS files for constitutional compliance"""
    
    print("🎨 CSS COMPLIANCE ANALYSIS")
    print("=" * 40)
    
    css_file = "static/css/constitutional-design.css"
    
    if not os.path.exists(css_file):
        print("❌ Constitutional CSS file not found")
        return False
    
    with open(css_file, 'r') as f:
        css_content = f.read()
    
    # Constitutional design requirements
    design_checks = {
        "Constitutional Color Palette": {
            "brown_primary": "#8B6F47" in css_content or "--const-brown-primary" in css_content,
            "olive_primary": "#6B8E23" in css_content or "--const-olive-primary" in css_content,
            "agricultural_green": "#228B22" in css_content or "var(--const-green" in css_content
        },
        "Typography Standards": {
            "minimum_18px": "--const-text-min: 18px" in css_content,
            "readable_fonts": "Segoe UI" in css_content or "Tahoma" in css_content,
            "line_height": "line-height: 1.6" in css_content or "--const-line-height" in css_content
        },
        "Spacing & Layout": {
            "consistent_spacing": "--const-spacing" in css_content,
            "16px_units": "16px" in css_content,
            "responsive_design": "@media" in css_content or "responsive" in css_content.lower()
        },
        "Agricultural Compliance": {
            "mango_rule": "mango" in css_content.lower(),
            "bulgarian_farmers": "bulgarian" in css_content.lower(),
            "farmer_accessibility": "farmer" in css_content.lower()
        }
    }
    
    total_checks = 0
    passed_checks = 0
    
    for category, checks in design_checks.items():
        print(f"\n📋 {category}:")
        category_passed = 0
        category_total = len(checks)
        
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}")
            if passed:
                category_passed += 1
            
        total_checks += category_total
        passed_checks += category_passed
        
        compliance_percent = (category_passed / category_total) * 100
        print(f"   📊 Category Score: {compliance_percent:.0f}%")
    
    overall_compliance = (passed_checks / total_checks) * 100
    print(f"\n📊 OVERALL CSS COMPLIANCE: {overall_compliance:.0f}%")
    
    return overall_compliance >= 90

def verify_template_consistency():
    """Verify templates use consistent constitutional design"""
    
    print("\n🏛️ TEMPLATE CONSISTENCY VERIFICATION")
    print("=" * 40)
    
    template_files = [
        "templates/base_constitutional.html",
        "templates/ui_dashboard_enhanced.html", 
        "templates/farmer_registration.html",
        "templates/register_fields.html",
        "templates/register_task.html",
        "templates/register_machinery.html",
        "templates/database_explorer_enhanced.html"
    ]
    
    consistent_elements = {
        "constitutional_css": "constitutional-design.css",
        "constitutional_classes": "const-",
        "agricultural_theme": "agricultural",
        "mango_compliance": "mango",
        "version_display": "current_version"
    }
    
    template_scores = {}
    
    for template_file in template_files:
        if not os.path.exists(template_file):
            print(f"⚠️  Missing: {os.path.basename(template_file)}")
            continue
        
        with open(template_file, 'r') as f:
            template_content = f.read().lower()
        
        score = 0
        total_elements = len(consistent_elements)
        
        for element_name, element_pattern in consistent_elements.items():
            if element_pattern.lower() in template_content:
                score += 1
        
        template_score = (score / total_elements) * 100
        template_scores[template_file] = template_score
        
        status = "✅" if template_score >= 80 else "❌"
        print(f"{status} {os.path.basename(template_file)}: {template_score:.0f}%")
    
    avg_template_score = sum(template_scores.values()) / len(template_scores) if template_scores else 0
    print(f"\n📊 AVERAGE TEMPLATE CONSISTENCY: {avg_template_score:.0f}%")
    
    return avg_template_score >= 80

def check_button_design_consistency():
    """Check button design across all templates"""
    
    print("\n🔘 BUTTON DESIGN CONSISTENCY")
    print("=" * 40)
    
    # Expected constitutional button patterns
    button_patterns = [
        r'class=".*constitutional.*button"',
        r'class=".*const-btn"',
        r'background:.*var\(--const-brown',
        r'font-size:.*var\(--const-text-min',
        r'padding:.*12px.*24px'
    ]
    
    template_files = Path(".").glob("templates/*.html")
    consistent_buttons = 0
    total_buttons = 0
    
    for template_file in template_files:
        with open(template_file, 'r') as f:
            content = f.read()
        
        # Find button elements
        buttons = re.findall(r'<button[^>]*>|<a[^>]*class="[^"]*btn[^"]*"', content, re.IGNORECASE)
        
        for button in buttons:
            total_buttons += 1
            
            # Check if button follows constitutional design
            constitutional_design = any(re.search(pattern, button, re.IGNORECASE) for pattern in button_patterns)
            
            if constitutional_design:
                consistent_buttons += 1
    
    if total_buttons > 0:
        button_consistency = (consistent_buttons / total_buttons) * 100
        print(f"✅ Constitutional Buttons: {consistent_buttons}/{total_buttons} ({button_consistency:.0f}%)")
        return button_consistency >= 75
    else:
        print("⚠️  No buttons found to analyze")
        return True

def verify_enter_key_support():
    """Verify Enter key support across all interactive elements"""
    
    print("\n⌨️  ENTER KEY SUPPORT VERIFICATION")
    print("=" * 40)
    
    template_files = Path(".").glob("templates/*.html")
    supported_elements = 0
    total_interactive = 0
    
    interactive_patterns = [
        r'<button[^>]*>',
        r'<input[^>]*type="submit"',
        r'<a[^>]*class="[^"]*btn[^"]*"'
    ]
    
    enter_support_patterns = [
        r'onkeypress="[^"]*Enter[^"]*"',
        r'addEventListener.*keypress',
        r'event\.key.*Enter'
    ]
    
    for template_file in template_files:
        with open(template_file, 'r') as f:
            content = f.read()
        
        # Find interactive elements
        for pattern in interactive_patterns:
            elements = re.findall(pattern, content, re.IGNORECASE)
            total_interactive += len(elements)
        
        # Check for Enter key support
        for pattern in enter_support_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                supported_elements += 1
                break  # Count once per file
    
    if total_interactive > 0:
        enter_support = (supported_elements / len(list(Path(".").glob("templates/*.html")))) * 100
        print(f"✅ Templates with Enter Support: {supported_elements}/{len(list(Path('.').glob('templates/*.html')))} ({enter_support:.0f}%)")
        return enter_support >= 70
    else:
        print("⚠️  No interactive elements found")
        return True

def generate_design_compliance_report():
    """Generate comprehensive design compliance report"""
    
    print("=" * 60)
    print("🏛️ CONSTITUTIONAL DESIGN COMPLIANCE REPORT")
    print("=" * 60)
    
    # Run all checks
    css_compliant = analyze_css_compliance()
    template_consistent = verify_template_consistency() 
    button_consistent = check_button_design_consistency()
    enter_supported = verify_enter_key_support()
    
    # Calculate overall score
    checks = [css_compliant, template_consistent, button_consistent, enter_supported]
    compliance_score = sum(checks) / len(checks) * 100
    
    print(f"\n📊 OVERALL DESIGN COMPLIANCE SCORE: {compliance_score:.0f}%")
    
    if compliance_score >= 95:
        print("🎉 EXCELLENT: Design fully compliant with constitutional standards!")
        print("🥭 Bulgarian Mango Farmer Design Approved")
        print("🏛️ Constitutional Principle #14 (Design-First): ACHIEVED")
        design_status = "EXCELLENT"
    elif compliance_score >= 80:
        print("✅ GOOD: Design substantially compliant")
        print("🔧 Minor improvements recommended")
        design_status = "GOOD"
    else:
        print("❌ NEEDS WORK: Design compliance insufficient")
        print("🚨 Immediate design fixes required")
        design_status = "NEEDS_WORK"
    
    # Save compliance report
    compliance_report = {
        "timestamp": "2025-01-19",
        "overall_score": compliance_score,
        "status": design_status,
        "checks": {
            "css_compliant": css_compliant,
            "template_consistent": template_consistent,
            "button_consistent": button_consistent,
            "enter_key_supported": enter_supported
        }
    }
    
    with open('design_compliance_report.json', 'w') as f:
        json.dump(compliance_report, f, indent=2)
    
    print(f"\n📄 Report saved to: design_compliance_report.json")
    
    return compliance_score >= 95

if __name__ == "__main__":
    success = generate_design_compliance_report()
    exit(0 if success else 1)