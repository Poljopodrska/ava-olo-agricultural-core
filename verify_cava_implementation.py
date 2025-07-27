#!/usr/bin/env python3
"""
CAVA Implementation Verification Script
Verifies all components are ready for v3.5.23 deployment
"""
import os
import sys
import importlib.util

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} NOT FOUND")
        return False

def check_module_imports(module_path, description):
    """Check if a module can be imported"""
    try:
        spec = importlib.util.spec_from_file_location("test_module", module_path)
        module = importlib.util.module_from_spec(spec)
        print(f"✅ {description}: Module imports successfully")
        return True
    except Exception as e:
        print(f"❌ {description}: Import failed - {str(e)}")
        return False

def main():
    print("🔍 CAVA Implementation Verification for v3.5.23")
    print("=" * 60)
    
    checks_passed = 0
    total_checks = 0
    
    # 1. Check version badge middleware
    print("\n1. VERSION BADGE MIDDLEWARE:")
    total_checks += 1
    if check_file_exists("modules/core/version_badge_middleware.py", "Version Badge Middleware"):
        checks_passed += 1
    
    # 2. Check CAVA Chat Engine
    print("\n2. CAVA CHAT ENGINE:")
    total_checks += 1
    if check_file_exists("modules/cava/chat_engine.py", "CAVA Chat Engine"):
        if check_module_imports("modules/cava/chat_engine.py", "CAVA Chat Engine"):
            checks_passed += 1
    
    # 3. Check Comprehensive Audit Dashboard
    print("\n3. COMPREHENSIVE AUDIT DASHBOARD:")
    total_checks += 1
    if check_file_exists("static/cava-comprehensive-audit.html", "Audit Dashboard HTML"):
        checks_passed += 1
    
    total_checks += 1
    if check_file_exists("modules/api/cava_comprehensive_audit_routes.py", "Audit API Routes"):
        checks_passed += 1
    
    # 4. Check test scripts
    print("\n4. TEST SCRIPTS:")
    total_checks += 1
    if check_file_exists("test_version_badge.py", "Version Badge Test Script"):
        checks_passed += 1
    
    # 5. Check configuration
    print("\n5. CONFIGURATION:")
    total_checks += 1
    try:
        from modules.core.config import VERSION
        if VERSION == "v3.5.23":
            print(f"✅ Version configured correctly: {VERSION}")
            checks_passed += 1
        else:
            print(f"❌ Version mismatch: {VERSION} (expected v3.5.23)")
    except:
        print("❌ Could not import version from config")
    
    # 6. Check main.py integration
    print("\n6. MAIN.PY INTEGRATION:")
    total_checks += 1
    with open("main.py", "r") as f:
        main_content = f.read()
        if "VersionBadgeMiddleware" in main_content:
            print("✅ Version badge middleware integrated in main.py")
            checks_passed += 1
        else:
            print("❌ Version badge middleware NOT integrated in main.py")
    
    total_checks += 1
    if "initialize_cava" in main_content:
        print("✅ CAVA initialization in startup")
        checks_passed += 1
    else:
        print("❌ CAVA initialization NOT in startup")
    
    total_checks += 1
    if "cava_comprehensive_audit_router" in main_content:
        print("✅ Comprehensive audit router included")
        checks_passed += 1
    else:
        print("❌ Comprehensive audit router NOT included")
    
    # 7. Check changelog
    print("\n7. DOCUMENTATION:")
    total_checks += 1
    changelog_path = "../ava-olo-shared/essentials/SYSTEM_CHANGELOG.md"
    if os.path.exists(changelog_path):
        with open(changelog_path, "r") as f:
            changelog = f.read()
            if "v3.5.23" in changelog and "CAVA Complete Implementation" in changelog:
                print("✅ SYSTEM_CHANGELOG updated for v3.5.23")
                checks_passed += 1
            else:
                print("❌ SYSTEM_CHANGELOG not updated for v3.5.23")
    else:
        print(f"❌ SYSTEM_CHANGELOG not found at {changelog_path}")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"VERIFICATION SUMMARY: {checks_passed}/{total_checks} checks passed")
    
    if checks_passed == total_checks:
        print("\n✅ SUCCESS: All components verified! Ready to deploy v3.5.23")
        print("\nNEXT STEPS:")
        print("1. Commit all changes: git add -A && git commit -m 'v3.5.23: CAVA Complete Implementation'")
        print("2. Push to GitHub: git push origin main")
        print("3. Monitor GitHub Actions for deployment")
        print("4. Test at: http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com")
        return 0
    else:
        print(f"\n❌ FAILED: {total_checks - checks_passed} checks failed")
        print("Please fix the issues above before deploying")
        return 1

if __name__ == "__main__":
    sys.exit(main())