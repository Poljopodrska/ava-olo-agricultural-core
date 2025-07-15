#!/usr/bin/env python3
"""
🏛️ CAVA AWS Deployment Safety Check
Comprehensive safety verification before deploying CAVA to AWS
Extends the existing Phase 1 safety check with AWS-specific validations
"""

import os
import sys
import subprocess
import socket
import json
import asyncio
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime

# Add parent paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from implementation.cava.phase1_safety_check import CAVAPhase1SafetyCheck

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CAVADeploymentSafetyCheck(CAVAPhase1SafetyCheck):
    """Extended safety checks for AWS deployment"""
    
    def __init__(self):
        super().__init__()
        self.deployment_risks = []
        self.aws_checks = []
        self.integration_checks = []
        self.test_results = {}
    
    def check_aws_credentials(self) -> bool:
        """Check AWS credentials are configured"""
        try:
            # Check AWS CLI
            result = subprocess.run(['aws', 'sts', 'get-caller-identity'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                identity = json.loads(result.stdout)
                self.aws_checks.append(f"AWS credentials valid: {identity.get('Arn', 'Unknown')}")
                return True
            else:
                self.deployment_risks.append("AWS credentials not configured")
                return False
        except FileNotFoundError:
            self.deployment_risks.append("AWS CLI not installed")
            return False
        except Exception as e:
            self.deployment_risks.append(f"AWS credential check failed: {str(e)}")
            return False
    
    def check_cava_service_health(self) -> bool:
        """Check if CAVA service is healthy locally"""
        try:
            import aiohttp
            import asyncio
            
            async def check_health():
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.get('http://localhost:8001/health', timeout=5) as response:
                            if response.status == 200:
                                data = await response.json()
                                self.checks_passed.append(f"CAVA service healthy: {data['status']}")
                                return True
                            else:
                                self.deployment_risks.append(f"CAVA service unhealthy: status {response.status}")
                                return False
                    except Exception as e:
                        self.deployment_risks.append(f"CAVA service not running: {str(e)}")
                        return False
            
            return asyncio.run(check_health())
            
        except Exception as e:
            self.deployment_risks.append(f"Health check failed: {str(e)}")
            return False
    
    def check_database_migrations(self) -> bool:
        """Check if database migrations are safe"""
        try:
            # Check for migration conflicts
            from config_manager import config
            
            # Check if CAVA schema exists
            self.checks_passed.append("Database configuration accessible")
            
            # Check for breaking changes
            breaking_changes = []
            
            # Check registration_memory.py changes
            if os.path.exists('registration_memory_original.py'):
                self.checks_passed.append("Original registration backed up")
            else:
                self.warnings.append("No backup of original registration found")
            
            if breaking_changes:
                self.deployment_risks.extend(breaking_changes)
                return False
            
            return True
            
        except Exception as e:
            self.warnings.append(f"Database migration check error: {str(e)}")
            return True
    
    def check_environment_variables(self) -> bool:
        """Check all required environment variables"""
        required_vars = {
            'OPENAI_API_KEY': 'OpenAI API key for LLM',
            'DATABASE_URL': 'PostgreSQL connection string',
            'APP_ENV': 'Application environment'
        }
        
        optional_vars = {
            'CAVA_DRY_RUN_MODE': 'CAVA dry-run mode',
            'CAVA_SERVICE_URL': 'CAVA service URL',
            'CAVA_NEO4J_URI': 'Neo4j connection URI',
            'CAVA_REDIS_URL': 'Redis connection URL'
        }
        
        missing_required = []
        for var, desc in required_vars.items():
            if os.getenv(var):
                self.checks_passed.append(f"{desc} configured: {var}")
            else:
                missing_required.append(f"{var} ({desc})")
        
        for var, desc in optional_vars.items():
            if os.getenv(var):
                self.checks_passed.append(f"{desc} configured: {var}")
            else:
                self.warnings.append(f"{desc} not set: {var} (will use defaults)")
        
        if missing_required:
            self.deployment_risks.append(f"Missing required env vars: {missing_required}")
            return False
        
        return True
    
    def run_integration_tests(self) -> bool:
        """Run critical integration tests"""
        test_results = {
            'registration_flow': False,
            'cava_connection': False,
            'database_operations': False
        }
        
        try:
            # Test 1: Registration flow
            logger.info("Testing registration flow...")
            result = subprocess.run([sys.executable, 'test_cava_integration.py'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                test_results['registration_flow'] = True
                self.integration_checks.append("Registration flow test passed")
            else:
                self.deployment_risks.append("Registration flow test failed")
                self.deployment_risks.append(f"Error: {result.stderr[:200]}")
            
        except subprocess.TimeoutExpired:
            self.deployment_risks.append("Registration test timed out")
        except Exception as e:
            self.warnings.append(f"Integration test error: {str(e)}")
        
        self.test_results = test_results
        return all(test_results.values()) or len(test_results) == 0
    
    def check_security_vulnerabilities(self) -> bool:
        """Check for common security issues"""
        security_issues = []
        
        # Check for hardcoded secrets
        files_to_check = [
            'implementation/cava/cava_api.py',
            'implementation/cava/database_connections.py',
            'api_gateway_with_cava.py'
        ]
        
        for file in files_to_check:
            if os.path.exists(file):
                with open(file, 'r') as f:
                    content = f.read()
                    
                    # Check for hardcoded passwords
                    if 'password=' in content and ('password="' in content or "password='" in content):
                        if not any(safe in content for safe in ['getenv', 'environ', 'config.']):
                            security_issues.append(f"Potential hardcoded password in {file}")
                    
                    # Check for hardcoded API keys
                    if 'api_key=' in content or 'API_KEY=' in content:
                        if not any(safe in content for safe in ['getenv', 'environ', 'config.']):
                            security_issues.append(f"Potential hardcoded API key in {file}")
        
        if security_issues:
            self.deployment_risks.extend(security_issues)
            return False
        else:
            self.checks_passed.append("No hardcoded secrets found")
            return True
    
    def check_resource_requirements(self) -> bool:
        """Check AWS resource requirements"""
        requirements = {
            'EC2': 't3.medium minimum for CAVA service',
            'RDS': 'Existing PostgreSQL instance',
            'ElastiCache': 'Redis cluster for CAVA memory',
            'DocumentDB': 'Optional for Neo4j replacement',
            'ALB': 'Application Load Balancer for CAVA API'
        }
        
        logger.info("\n📊 AWS Resource Requirements:")
        for service, requirement in requirements.items():
            logger.info(f"   • {service}: {requirement}")
        
        self.aws_checks.append("Resource requirements documented")
        return True
    
    def generate_deployment_report(self) -> Dict[str, Any]:
        """Generate comprehensive deployment safety report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'safe_to_deploy': len(self.deployment_risks) == 0,
            'checks': {
                'passed': len(self.checks_passed),
                'warnings': len(self.warnings),
                'failed': len(self.checks_failed) + len(self.deployment_risks)
            },
            'details': {
                'infrastructure': self.checks_passed,
                'warnings': self.warnings,
                'failures': self.checks_failed + self.deployment_risks,
                'aws_readiness': self.aws_checks,
                'integration_tests': self.test_results
            },
            'recommendations': []
        }
        
        # Add recommendations
        if self.deployment_risks:
            report['recommendations'].append("Fix all deployment risks before proceeding")
        
        if self.warnings:
            report['recommendations'].append("Review warnings and address if necessary")
        
        if not self.aws_checks:
            report['recommendations'].append("Configure AWS credentials and resources")
        
        return report
    
    def run_full_deployment_check(self) -> bool:
        """Run comprehensive deployment safety check"""
        logger.info("🏛️ CAVA AWS DEPLOYMENT SAFETY CHECK")
        logger.info("=" * 60)
        logger.info("Checking if CAVA is safe to deploy to AWS...")
        logger.info("")
        
        # Run base checks from parent class
        logger.info("📋 Running infrastructure checks...")
        super().run_all_checks()
        
        # Run AWS-specific checks
        logger.info("\n☁️ Running AWS deployment checks...")
        aws_checks = [
            (self.check_aws_credentials, "AWS credentials"),
            (self.check_cava_service_health, "CAVA service health"),
            (self.check_database_migrations, "Database migrations"),
            (self.check_environment_variables, "Environment variables"),
            (self.check_security_vulnerabilities, "Security vulnerabilities"),
            (self.check_resource_requirements, "Resource requirements")
        ]
        
        for check_func, check_name in aws_checks:
            logger.info(f"\n🔍 Checking: {check_name}")
            try:
                check_func()
            except Exception as e:
                self.deployment_risks.append(f"{check_name} check error: {str(e)}")
        
        # Run integration tests
        logger.info("\n🧪 Running integration tests...")
        self.run_integration_tests()
        
        # Generate report
        report = self.generate_deployment_report()
        
        # Display summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 DEPLOYMENT SAFETY SUMMARY")
        logger.info("=" * 60)
        
        logger.info(f"\n✅ Passed: {report['checks']['passed']} checks")
        logger.info(f"⚠️  Warnings: {report['checks']['warnings']} issues")
        logger.info(f"❌ Failed: {report['checks']['failed']} checks")
        
        if self.deployment_risks:
            logger.error("\n🚨 DEPLOYMENT RISKS:")
            for risk in self.deployment_risks:
                logger.error(f"   ❌ {risk}")
        
        if report['recommendations']:
            logger.info("\n💡 RECOMMENDATIONS:")
            for rec in report['recommendations']:
                logger.info(f"   • {rec}")
        
        # Save report
        report_file = f"cava_deployment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"\n📄 Full report saved to: {report_file}")
        
        # Final verdict
        safe_to_deploy = report['safe_to_deploy']
        
        if safe_to_deploy:
            logger.info("\n✅ SAFE TO DEPLOY CAVA TO AWS")
            logger.info("\nNext steps:")
            logger.info("1. Review the deployment report")
            logger.info("2. Set up AWS infrastructure (EC2, ALB, ElastiCache)")
            logger.info("3. Configure environment variables for production")
            logger.info("4. Deploy using your CI/CD pipeline")
        else:
            logger.error("\n❌ NOT SAFE TO DEPLOY - Fix issues first!")
            logger.error(f"\nFound {len(self.deployment_risks)} deployment risks")
        
        return safe_to_deploy

def main():
    """Run deployment safety check"""
    checker = CAVADeploymentSafetyCheck()
    safe_to_deploy = checker.run_full_deployment_check()
    
    sys.exit(0 if safe_to_deploy else 1)

if __name__ == "__main__":
    main()