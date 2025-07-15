#!/usr/bin/env python3
"""
🏛️ Comprehensive Deployment Safety Check
Checks both main application and CAVA enhancements
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeploymentSafetyChecker:
    """Comprehensive deployment safety checks"""
    
    def __init__(self):
        self.checks_passed = []
        self.checks_failed = []
        self.warnings = []
        
    def run_all_checks(self) -> Tuple[bool, Dict]:
        """Run all deployment safety checks"""
        logger.info("🏛️ COMPREHENSIVE DEPLOYMENT SAFETY CHECK")
        logger.info("=" * 60)
        
        # Check categories
        self.check_code_quality()
        self.check_cava_enhancements()
        self.check_dependencies()
        self.check_configuration()
        self.check_docker_setup()
        self.check_database_safety()
        self.check_api_endpoints()
        
        # Generate report
        report = self.generate_report()
        
        # Determine if safe to deploy
        is_safe = len(self.checks_failed) == 0
        
        return is_safe, report
    
    def check_code_quality(self):
        """Check code quality and imports"""
        logger.info("\n📝 Checking code quality...")
        
        # Check for TODO/FIXME comments
        critical_files = [
            "api_gateway_simple.py",
            "implementation/cava/universal_conversation_engine.py",
            "implementation/cava/database_connections.py",
            "implementation/cava/error_handling.py",
            "implementation/cava/performance_optimization.py"
        ]
        
        for file in critical_files:
            if os.path.exists(file):
                try:
                    with open(file, 'r') as f:
                        content = f.read()
                        if 'TODO' in content or 'FIXME' in content:
                            self.warnings.append(f"Found TODO/FIXME in {file}")
                        else:
                            self.checks_passed.append(f"No TODO/FIXME in {file}")
                except Exception as e:
                    self.warnings.append(f"Could not check {file}: {e}")
    
    def check_cava_enhancements(self):
        """Check CAVA 10/10 enhancements"""
        logger.info("\n🎯 Checking CAVA enhancements...")
        
        # Enhancement 1: Vector Intelligence
        vector_files = [
            "implementation/cava/database_connections.py"
        ]
        for file in vector_files:
            if os.path.exists(file):
                with open(file, 'r') as f:
                    content = f.read()
                    if 'generate_embedding' in content and 'search_similar_conversations' in content:
                        self.checks_passed.append("✅ Vector intelligence implemented")
                    else:
                        self.checks_failed.append("❌ Vector intelligence incomplete")
        
        # Enhancement 2: Error Handling
        if os.path.exists("implementation/cava/error_handling.py"):
            self.checks_passed.append("✅ Error handling module exists")
        else:
            self.checks_failed.append("❌ Error handling module missing")
        
        # Enhancement 3: Performance Optimization
        if os.path.exists("implementation/cava/performance_optimization.py"):
            self.checks_passed.append("✅ Performance optimization module exists")
        else:
            self.checks_failed.append("❌ Performance optimization module missing")
    
    def check_dependencies(self):
        """Check Python dependencies"""
        logger.info("\n📦 Checking dependencies...")
        
        required_packages = [
            "fastapi",
            "uvicorn",
            "redis",
            "asyncpg",
            "neo4j",
            "openai",
            "pydantic",
            "python-dotenv"
        ]
        
        try:
            import pkg_resources
            installed_packages = {pkg.key for pkg in pkg_resources.working_set}
            
            for package in required_packages:
                if package in installed_packages:
                    self.checks_passed.append(f"✅ {package} installed")
                else:
                    self.checks_failed.append(f"❌ {package} not installed")
        except Exception as e:
            self.warnings.append(f"Could not check packages: {e}")
    
    def check_configuration(self):
        """Check configuration files"""
        logger.info("\n⚙️ Checking configuration...")
        
        # Check environment files
        if os.path.exists(".env"):
            self.checks_passed.append("✅ Main .env file exists")
        else:
            self.checks_failed.append("❌ Main .env file missing")
        
        # Check critical environment variables
        critical_vars = [
            "OPENAI_API_KEY",
            "DATABASE_URL",
            "CAVA_INTEGRATED_MODE",
            "CAVA_DRY_RUN_MODE"
        ]
        
        for var in critical_vars:
            if os.getenv(var):
                self.checks_passed.append(f"✅ {var} configured")
            else:
                self.warnings.append(f"⚠️ {var} not set")
    
    def check_docker_setup(self):
        """Check Docker configuration"""
        logger.info("\n🐳 Checking Docker setup...")
        
        if os.path.exists("Dockerfile"):
            with open("Dockerfile", 'r') as f:
                content = f.read()
                if "CMD" in content and "uvicorn" in content:
                    self.checks_passed.append("✅ Dockerfile configured correctly")
                else:
                    self.checks_failed.append("❌ Dockerfile misconfigured")
        else:
            self.checks_failed.append("❌ Dockerfile missing")
        
        # Check if we're using App Runner (not apprunner.yaml)
        if os.path.exists("README_APPRUNNER.md"):
            self.checks_passed.append("✅ App Runner configuration found")
        else:
            self.warnings.append("⚠️ App Runner documentation missing")
    
    def check_database_safety(self):
        """Check database safety"""
        logger.info("\n🗄️ Checking database safety...")
        
        # Check for hardcoded credentials
        files_to_check = [
            "api_gateway_simple.py",
            "config_manager.py",
            "implementation/cava/database_connections.py"
        ]
        
        for file in files_to_check:
            if os.path.exists(file):
                with open(file, 'r') as f:
                    content = f.read()
                    if "password=" in content and "os.getenv" not in content:
                        self.checks_failed.append(f"❌ Possible hardcoded password in {file}")
                    else:
                        self.checks_passed.append(f"✅ No hardcoded passwords in {file}")
    
    def check_api_endpoints(self):
        """Check API endpoints"""
        logger.info("\n🌐 Checking API endpoints...")
        
        if os.path.exists("api_gateway_simple.py"):
            with open("api_gateway_simple.py", 'r') as f:
                content = f.read()
                if "cava_router" in content:
                    self.checks_passed.append("✅ CAVA routes integrated")
                else:
                    self.checks_failed.append("❌ CAVA routes not integrated")
        
        # Check new performance endpoint
        if os.path.exists("api/cava_routes.py"):
            with open("api/cava_routes.py", 'r') as f:
                content = f.read()
                if "/performance" in content:
                    self.checks_passed.append("✅ Performance endpoint added")
                else:
                    self.warnings.append("⚠️ Performance endpoint missing")
    
    def generate_report(self) -> Dict:
        """Generate deployment report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_checks": len(self.checks_passed) + len(self.checks_failed),
                "passed": len(self.checks_passed),
                "failed": len(self.checks_failed),
                "warnings": len(self.warnings)
            },
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "warnings": self.warnings,
            "recommendations": []
        }
        
        # Add recommendations
        if self.checks_failed:
            report["recommendations"].append("Fix all failed checks before deployment")
        
        if self.warnings:
            report["recommendations"].append("Review warnings and address if critical")
        
        if "CAVA_DRY_RUN_MODE" in str(self.warnings):
            report["recommendations"].append("Set CAVA_DRY_RUN_MODE=false for production")
        
        if "Docker" in str(self.checks_failed):
            report["recommendations"].append("Docker is not required for App Runner deployment")
        
        return report
    
    def print_summary(self, is_safe: bool, report: Dict):
        """Print summary to console"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 DEPLOYMENT SAFETY SUMMARY")
        logger.info("=" * 60)
        
        logger.info(f"\n✅ Passed: {report['summary']['passed']} checks")
        if report['warnings']:
            logger.info(f"⚠️  Warnings: {report['summary']['warnings']} issues")
        if report['checks_failed']:
            logger.error(f"❌ Failed: {report['summary']['failed']} checks")
        
        if report['checks_failed']:
            logger.error("\n🚨 FAILED CHECKS:")
            for check in report['checks_failed']:
                logger.error(f"   {check}")
        
        if report['warnings']:
            logger.warning("\n⚠️  WARNINGS:")
            for warning in report['warnings']:
                logger.warning(f"   {warning}")
        
        if report['recommendations']:
            logger.info("\n💡 RECOMMENDATIONS:")
            for rec in report['recommendations']:
                logger.info(f"   • {rec}")
        
        # Save report
        report_file = f"deployment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"\n📄 Full report saved to: {report_file}")
        
        if is_safe:
            logger.info("\n✅ SAFE TO DEPLOY!")
            logger.info("\nNext steps:")
            logger.info("1. git add .")
            logger.info("2. git commit -m 'feat: CAVA 10/10 enhancements - vector intelligence, error handling, performance'")
            logger.info("3. git push")
            logger.info("4. AWS App Runner will automatically deploy")
        else:
            logger.error("\n❌ NOT SAFE TO DEPLOY - Fix issues first!")
            logger.error(f"\nFound {report['summary']['failed']} failed checks")

def main():
    """Run deployment safety check"""
    checker = DeploymentSafetyChecker()
    is_safe, report = checker.run_all_checks()
    checker.print_summary(is_safe, report)
    
    # Exit with appropriate code
    sys.exit(0 if is_safe else 1)

if __name__ == "__main__":
    main()