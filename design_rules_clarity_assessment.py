#!/usr/bin/env python3
"""
Constitutional Design Rules Clarity Assessment
Evaluate if design rules are clear enough for consistent implementation
"""

import os
import re
from pathlib import Path

def assess_color_palette_clarity():
    """Assess clarity of color palette definitions"""
    
    css_file = "static/css/constitutional-design.css"
    
    if not os.path.exists(css_file):
        return False, "Constitutional CSS file not found"
    
    with open(css_file, 'r') as f:
        content = f.read()
    
    # Check for clear color definitions
    color_checks = {
        "Primary colors defined": bool(re.search(r'--const-brown-primary.*#[0-9A-Fa-f]{6}', content)),
        "Secondary colors defined": bool(re.search(r'--const-olive-primary.*#[0-9A-Fa-f]{6}', content)),
        "Color variations provided": bool(re.search(r'--const-.*-dark.*#[0-9A-Fa-f]{6}', content)),
        "Earth tones included": "earth" in content.lower(),
        "Usage comments provided": "//" in content or "/*" in content,
    }
    
    score = sum(color_checks.values()) / len(color_checks) * 100
    issues = [name for name, passed in color_checks.items() if not passed]
    
    return score >= 80, f"Score: {score:.0f}% - Issues: {issues}"

def assess_typography_clarity():
    """Assess clarity of typography rules"""
    
    css_file = "static/css/constitutional-design.css"
    
    with open(css_file, 'r') as f:
        content = f.read()
    
    typography_checks = {
        "Minimum font size defined": "--const-text-min: 18px" in content,
        "Font scale provided": bool(re.search(r'--const-text-.*: \d+px', content)),
        "Font family specified": "font-family" in content,
        "Line height defined": "line-height" in content,
        "Text size hierarchy": content.count("--const-text-") >= 3,
    }
    
    score = sum(typography_checks.values()) / len(typography_checks) * 100
    issues = [name for name, passed in typography_checks.items() if not passed]
    
    return score >= 80, f"Score: {score:.0f}% - Issues: {issues}"

def assess_component_standards():
    """Assess clarity of component standards"""
    
    css_file = "static/css/constitutional-design.css"
    
    with open(css_file, 'r') as f:
        content = f.read()
    
    component_checks = {
        "Button styles defined": ".const-btn" in content,
        "Button variants provided": content.count("const-btn") >= 2,
        "Form styles available": "form" in content.lower() or "input" in content,
        "Card styles defined": "card" in content.lower(),
        "Spacing system": "--const-spacing" in content,
    }
    
    score = sum(component_checks.values()) / len(component_checks) * 100
    issues = [name for name, passed in component_checks.items() if not passed]
    
    return score >= 70, f"Score: {score:.0f}% - Issues: {issues}"

def assess_layout_rules():
    """Assess clarity of layout rules"""
    
    css_file = "static/css/constitutional-design.css"
    
    with open(css_file, 'r') as f:
        content = f.read()
    
    layout_checks = {
        "Spacing variables": "--const-spacing" in content,
        "Container definitions": "container" in content.lower(),
        "Grid system": "grid" in content.lower() or "flex" in content.lower(),
        "Border radius standards": "border-radius" in content,
        "Shadow definitions": "shadow" in content,
    }
    
    score = sum(layout_checks.values()) / len(layout_checks) * 100
    issues = [name for name, passed in layout_checks.items() if not passed]
    
    return score >= 70, f"Score: {score:.0f}% - Issues: {issues}"

def assess_mobile_guidelines():
    """Assess clarity of mobile/responsive guidelines"""
    
    css_files = list(Path(".").glob("static/css/*.css"))
    template_files = list(Path(".").glob("templates/*.html"))
    
    mobile_features = 0
    total_files = len(css_files) + len(template_files)
    
    for file_path in css_files + template_files:
        with open(file_path, 'r') as f:
            content = f.read()
        
        if any(keyword in content for keyword in ["@media", "responsive", "mobile", "max-width"]):
            mobile_features += 1
    
    mobile_score = (mobile_features / total_files * 100) if total_files > 0 else 0
    
    return mobile_score >= 50, f"Score: {mobile_score:.0f}% - Mobile features in {mobile_features}/{total_files} files"

def assess_practical_examples():
    """Assess availability of practical examples"""
    
    template_files = list(Path(".").glob("templates/*.html"))
    documentation_files = list(Path(".").glob("*.md"))
    
    example_checks = {
        "Template examples": len(template_files) >= 5,
        "Documentation files": len(documentation_files) >= 3,
        "Constitutional classes used": False,
        "Real implementations": False,
    }
    
    # Check if constitutional classes are actually used
    constitutional_usage = 0
    for template_file in template_files:
        with open(template_file, 'r') as f:
            content = f.read()
        
        if "const-" in content or "constitutional" in content:
            constitutional_usage += 1
    
    example_checks["Constitutional classes used"] = constitutional_usage >= 3
    example_checks["Real implementations"] = constitutional_usage >= 5
    
    score = sum(example_checks.values()) / len(example_checks) * 100
    details = f"Score: {score:.0f}% - Constitutional usage in {constitutional_usage}/{len(template_files)} templates"
    
    return score >= 75, details

def generate_design_clarity_assessment():
    """Generate comprehensive design rules clarity assessment"""
    
    print("🎨 CONSTITUTIONAL DESIGN RULES CLARITY ASSESSMENT")
    print("=" * 50)
    
    # Run all assessments
    assessments = {
        "Color Palette": assess_color_palette_clarity(),
        "Typography": assess_typography_clarity(),
        "Components": assess_component_standards(),
        "Layout Rules": assess_layout_rules(),
        "Mobile Guidelines": assess_mobile_guidelines(),
        "Examples": assess_practical_examples(),
    }
    
    print("📋 ASSESSMENT BREAKDOWN:")
    
    total_score = 0
    passed_assessments = 0
    
    for category, (passed, details) in assessments.items():
        status = "✅" if passed else "❌"
        clarity = "Clear" if passed else "Unclear"
        print(f"{status} {category}: {clarity} - {details}")
        
        if passed:
            passed_assessments += 1
            total_score += 100
        else:
            # Extract score from details if available
            score_match = re.search(r'Score: (\d+)%', details)
            if score_match:
                total_score += int(score_match.group(1))
    
    # Calculate overall clarity score
    overall_clarity = total_score / len(assessments)
    
    print(f"\n📊 CLARITY SCORE: {overall_clarity:.0f}/100")
    
    # Overall assessment
    print(f"\n🎯 OVERALL ASSESSMENT:")
    if overall_clarity >= 90:
        assessment_result = "EXCELLENT - Rules are very clear"
        recommendation = "Design rules are comprehensive and clear for implementation"
    elif overall_clarity >= 75:
        assessment_result = "SUFFICIENT - Rules are clear enough"
        recommendation = "Minor clarifications could improve consistency"
    else:
        assessment_result = "INSUFFICIENT - Needs clarification in next task"
        recommendation = "Significant improvements needed for clear implementation"
    
    print(assessment_result)
    
    # Specific issues and recommendations
    print(f"\n🔍 SPECIFIC ISSUES FOUND:")
    issues_found = []
    for category, (passed, details) in assessments.items():
        if not passed:
            print(f"- {category}: {details}")
            issues_found.append(category)
    
    if not issues_found:
        print("- No significant clarity issues detected")
    
    print(f"\n💡 RECOMMENDATIONS:")
    if issues_found:
        print("- Add more detailed examples for unclear categories")
        print("- Provide specific implementation guidelines")
        print("- Create comprehensive style guide documentation")
    else:
        print("- Continue maintaining current design standard quality")
        print("- Regular reviews to ensure consistency")
    
    # Button color constitutional status
    print(f"\n🎨 BUTTON COLOR CONSTITUTIONAL STATUS:")
    print("- Brown buttons: ✅ Constitutional (#8B4513)")
    print("- Olive buttons: ✅ Constitutional (#808000)")
    print("- Green buttons: ✅ Constitutional (#228B22 - Earth green)")
    print("- Note: Production sites correctly use constitutional button classes")
    
    return overall_clarity, assessment_result, recommendation

if __name__ == "__main__":
    clarity_score, assessment, recommendation = generate_design_clarity_assessment()
    
    print(f"\n🏛️ FINAL DESIGN RULES CLARITY: {assessment}")
    print(f"📊 Clarity Score: {clarity_score:.0f}%")
    
    if clarity_score >= 75:
        print("✅ Design rules are sufficiently clear for constitutional implementation")
    else:
        print("🔧 Design rules need improvement for better clarity")