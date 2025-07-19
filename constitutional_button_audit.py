#!/usr/bin/env python3
"""
Constitutional Button Color Audit
Check all button colors against constitutional standards
"""

import os
import re
import requests
from pathlib import Path

def audit_button_colors():
    """Check all button colors against constitutional standards"""
    
    print("🎨 CONSTITUTIONAL BUTTON COLOR AUDIT")
    print("=" * 50)
    
    # Constitutional color definitions
    constitutional_colors = {
        'primary_brown': '#8B4513',     # Constitutional brown
        'secondary_olive': '#808000',   # Constitutional olive  
        'earth_green': '#228B22',       # Earth green
        'brown_dark': '#6B5637',        # Dark brown
        'olive_dark': '#556B2F',        # Dark olive
    }
    
    print("📋 Constitutional Color Palette:")
    for name, color in constitutional_colors.items():
        print(f"  ✅ {name}: {color}")
    
    # Audit CSS files
    css_files = list(Path(".").glob("static/css/*.css"))
    template_files = list(Path(".").glob("templates/*.html"))
    
    print(f"\n🔍 Auditing {len(css_files)} CSS files and {len(template_files)} templates...")
    
    button_colors_found = []
    non_constitutional_colors = []
    
    # Check CSS files
    for css_file in css_files:
        with open(css_file, 'r') as f:
            content = f.read()
        
        # Find button color definitions
        button_patterns = [
            r'\..*btn.*\{[^}]*background[^}]*\}',
            r'\..*button.*\{[^}]*background[^}]*\}',
            r'\.constitutional-.*\{[^}]*background[^}]*\}',
        ]
        
        for pattern in button_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                # Extract color values
                color_matches = re.findall(r'#[0-9A-Fa-f]{6}|rgb\([^)]+\)|rgba\([^)]+\)', match)
                for color in color_matches:
                    button_colors_found.append({
                        'file': str(css_file),
                        'color': color,
                        'context': match[:100].replace('\n', ' ')
                    })
    
    # Check template files for inline styles
    for template_file in template_files:
        with open(template_file, 'r') as f:
            content = f.read()
        
        # Find inline button styles
        inline_patterns = [
            r'style="[^"]*background[^"]*"',
            r'style=\'[^\']*background[^\']*\'',
        ]
        
        for pattern in inline_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                # Extract color values
                color_matches = re.findall(r'#[0-9A-Fa-f]{6}|rgb\([^)]+\)|rgba\([^)]+\)', match)
                for color in color_matches:
                    button_colors_found.append({
                        'file': str(template_file),
                        'color': color,
                        'context': match[:100]
                    })
    
    print(f"\n📊 Found {len(button_colors_found)} button color definitions")
    
    # Analyze colors for constitutional compliance
    constitutional_hex_colors = list(constitutional_colors.values())
    
    print("\n🔍 Color Analysis:")
    for item in button_colors_found:
        color = item['color'].upper()
        is_constitutional = any(const_color.upper() in color for const_color in constitutional_hex_colors)
        
        # Special checks
        is_green = any(green in color.lower() for green in ['#228B22', '#22', 'green'])
        is_variable = 'var(' in color or '--const-' in color
        
        status = "✅" if (is_constitutional or is_variable) else "❌"
        print(f"  {status} {color} in {os.path.basename(item['file'])}")
        
        if not (is_constitutional or is_variable):
            non_constitutional_colors.append(item)
    
    return analyze_button_compliance(constitutional_colors, button_colors_found, non_constitutional_colors)

def analyze_button_compliance(constitutional_colors, found_colors, non_constitutional):
    """Analyze overall button color compliance"""
    
    print(f"\n📊 COMPLIANCE ANALYSIS")
    print("=" * 30)
    
    total_colors = len(found_colors)
    constitutional_count = total_colors - len(non_constitutional)
    compliance_score = (constitutional_count / total_colors * 100) if total_colors > 0 else 100
    
    print(f"Total button colors found: {total_colors}")
    print(f"Constitutional colors: {constitutional_count}")
    print(f"Non-constitutional colors: {len(non_constitutional)}")
    print(f"Compliance score: {compliance_score:.0f}%")
    
    # Green button assessment
    green_buttons = [item for item in found_colors if '#228B22' in item['color'].upper() or 'green' in item['color'].lower()]
    
    print(f"\n🟢 GREEN BUTTON ASSESSMENT:")
    if green_buttons:
        print(f"Found {len(green_buttons)} green button(s)")
        
        # Check if #228B22 is in constitutional colors
        earth_green = '#228B22'
        if earth_green in constitutional_colors.values():
            print(f"✅ Green buttons ({earth_green}) are CONSTITUTIONAL")
            print("   Reason: Listed as 'earth_green' in constitutional palette")
        else:
            print(f"❌ Green buttons ({earth_green}) may not be constitutional")
            print("   Recommendation: Verify against design principles")
    else:
        print("No green buttons found")
    
    # Specific issues
    if non_constitutional:
        print(f"\n🚨 NON-CONSTITUTIONAL COLORS FOUND:")
        for item in non_constitutional[:5]:  # Show first 5
            print(f"  ❌ {item['color']} in {os.path.basename(item['file'])}")
            print(f"     Context: {item['context'][:60]}...")
    
    # Overall assessment
    print(f"\n🏛️ CONSTITUTIONAL ASSESSMENT:")
    if compliance_score >= 95:
        print("✅ EXCELLENT: Button colors fully constitutional")
        return "EXCELLENT"
    elif compliance_score >= 80:
        print("✅ GOOD: Minor color issues detected")
        return "GOOD"
    else:
        print("❌ NEEDS WORK: Significant color violations found")
        return "NEEDS_WORK"

def check_production_button_colors():
    """Check button colors on production site"""
    
    print(f"\n🌐 PRODUCTION BUTTON COLOR CHECK")
    print("=" * 40)
    
    pages_to_check = [
        '/',
        '/farmer-registration',
        '/database-explorer',
        '/register-fields'
    ]
    
    base_url = "https://6pmgrirjre.us-east-1.awsapprunner.com"
    
    for page in pages_to_check:
        try:
            response = requests.get(f"{base_url}{page}", timeout=10)
            if response.status_code == 200:
                content = response.text
                
                # Check for constitutional button classes
                constitutional_buttons = [
                    'constitutional-submit-button',
                    'const-btn',
                    'const-btn-primary',
                    'constitutional-button'
                ]
                
                found_constitutional = sum(1 for btn_class in constitutional_buttons if btn_class in content)
                
                # Check for non-constitutional colors
                problematic_colors = ['#00FF00', 'lime', 'rgb(0,255,0)', '#FF0000']
                found_problematic = sum(1 for color in problematic_colors if color.lower() in content.lower())
                
                status = "✅" if found_constitutional > 0 and found_problematic == 0 else "⚠️"
                print(f"  {status} {page}: {found_constitutional} constitutional buttons, {found_problematic} issues")
                
            else:
                print(f"  ❌ {page}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ {page}: ERROR {str(e)}")

if __name__ == "__main__":
    compliance_status = audit_button_colors()
    check_production_button_colors()
    
    print(f"\n🎯 FINAL BUTTON COLOR AUDIT RESULT: {compliance_status}")
    
    if compliance_status in ["EXCELLENT", "GOOD"]:
        print("🏛️ Constitutional button color compliance achieved!")
    else:
        print("🔧 Button color fixes required for constitutional compliance")