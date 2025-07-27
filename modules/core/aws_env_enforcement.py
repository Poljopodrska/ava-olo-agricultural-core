#!/usr/bin/env python3
"""
AWS Environment Variable Enforcement System
Ensures ALL environment variables come from AWS only - NEVER local files
Part of the Complete Protection System v3.5.5
"""
import os
import sys
import re
from typing import Dict, Any, List
from pathlib import Path

class AWSEnvironmentEnforcer:
    """Ensures ALL environment variables come from AWS only"""
    
    # Whitelist of allowed default values (non-sensitive only)
    ALLOWED_DEFAULTS = {
        'APP_VERSION': 'development',
        'ENVIRONMENT': 'production', 
        'AWS_REGION': 'us-east-1',
        'PORT': '8080',
        'SERVICE_NAME': 'unknown'
    }
    
    # Critical variables that MUST come from AWS
    CRITICAL_AWS_VARS = [
        'DB_PASSWORD',
        'OPENAI_API_KEY',
        'OPENWEATHER_API_KEY',
        'GOOGLE_MAPS_API_KEY',
        'SECRET_KEY',
        'JWT_SECRET_KEY'
    ]
    
    @classmethod
    def enforce_aws_only(cls):
        """Block execution if running with local .env file or hardcoded secrets"""
        
        # Check for .env file in current directory and parent directories
        env_files = cls.find_env_files()
        if env_files:
            print("❌ FATAL ERROR: .env file(s) detected!")
            print("Environment variables MUST come from AWS ECS task definitions")
            print("Found .env files:")
            for env_file in env_files:
                print(f"  - {env_file}")
            print("")
            print("🏛️ Constitutional Rule: All secrets in AWS only (Principle 8)")
            print("🔧 Solution: Delete .env files and use AWS ECS environment variables")
            sys.exit(1)
        
        # Check if running in AWS
        aws_status = cls.is_running_in_aws()
        if not aws_status:
            print("⚠️  WARNING: Not running in AWS environment")
            print("Local development detected - some features may not work")
            print("Production requires AWS ECS with environment variables")
        else:
            print("✅ Running in AWS environment - secrets secure")
    
    @classmethod
    def find_env_files(cls) -> List[str]:
        """Find any .env files in current or parent directories"""
        env_files = []
        current_dir = Path.cwd()
        
        # Check current directory and up to 3 parent directories
        for _ in range(4):
            for pattern in ['.env', '.env.*', '*.env', 'environment.*']:
                env_files.extend([str(f) for f in current_dir.glob(pattern) if f.is_file()])
            
            if current_dir.parent == current_dir:  # Reached root
                break
            current_dir = current_dir.parent
        
        return env_files
    
    @classmethod
    def is_running_in_aws(cls) -> bool:
        """Detect if running in AWS ECS"""
        aws_indicators = [
            'ECS_CONTAINER_METADATA_URI',
            'ECS_CONTAINER_METADATA_URI_V4',
            'AWS_EXECUTION_ENV',
            'AWS_CONTAINER_CREDENTIALS_RELATIVE_URI',
            'AWS_BATCH_JOB_ID'
        ]
        
        # Check for AWS environment indicators
        aws_env_count = sum(1 for indicator in aws_indicators if os.getenv(indicator))
        
        # Also check for common AWS values
        aws_region = os.getenv('AWS_REGION', '')
        aws_account = os.getenv('AWS_ACCOUNT_ID', '')
        
        return aws_env_count > 0 or 'aws' in aws_region.lower()
    
    @classmethod
    def validate_no_hardcoded_values(cls, config_dict: Dict[str, Any]):
        """Ensure no hardcoded sensitive values"""
        
        forbidden_patterns = [
            (r'sk-[a-zA-Z0-9]{20,}', 'OpenAI API key'),
            (r'pk_[a-zA-Z0-9]+', 'Stripe public key'),
            (r'sk_[a-zA-Z0-9]+', 'Stripe secret key'),
            (r'xoxb-[a-zA-Z0-9]+', 'Slack bot token'),
            (r'ghp_[a-zA-Z0-9]+', 'GitHub personal access token'),
            (r'gho_[a-zA-Z0-9]+', 'GitHub OAuth token'),
            (r'AIza[a-zA-Z0-9_-]{35}', 'Google API key'),
            (r'ya29\.[a-zA-Z0-9_-]+', 'Google OAuth token'),
            (r'[a-f0-9]{32}', 'Generic 32-char hash (potential secret)'),
        ]
        
        violations = []
        
        for key, value in config_dict.items():
            if value and isinstance(value, str):
                for pattern, description in forbidden_patterns:
                    if re.search(pattern, str(value)):
                        violations.append(f"❌ Hardcoded {description} detected in {key}!")
        
        if violations:
            print("❌ FATAL ERROR: Hardcoded secrets detected!")
            for violation in violations:
                print(f"  {violation}")
            print("")
            print("🏛️ Constitutional Rule: No hardcoded secrets (Principle 8)")
            print("🔧 Solution: Move secrets to AWS ECS environment variables")
            raise ValueError("Hardcoded secrets are forbidden")
    
    @classmethod
    def validate_critical_vars_from_aws(cls):
        """Ensure critical variables are available (presumably from AWS)"""
        missing_critical = []
        
        for var_name in cls.CRITICAL_AWS_VARS:
            if not os.getenv(var_name):
                missing_critical.append(var_name)
        
        if missing_critical:
            if cls.is_running_in_aws():
                print(f"❌ FATAL: Missing critical environment variables in AWS:")
                for var in missing_critical:
                    print(f"  - {var}")
                print("")
                print("🔧 Solution: Add missing variables to AWS ECS task definition")
                raise EnvironmentError("Critical AWS environment variables missing")
            else:
                print(f"⚠️  Local development: Missing AWS environment variables:")
                for var in missing_critical:
                    print(f"  - {var}")
                print("These are required in AWS ECS for production")
    
    @classmethod 
    def get_environment_security_status(cls) -> Dict[str, Any]:
        """Get comprehensive environment security status"""
        env_files = cls.find_env_files()
        aws_running = cls.is_running_in_aws()
        
        missing_critical = [var for var in cls.CRITICAL_AWS_VARS if not os.getenv(var)]
        
        # Overall security assessment
        if env_files:
            security_level = "CRITICAL_VIOLATION"
        elif missing_critical and aws_running:
            security_level = "AWS_MISCONFIGURED"
        elif not aws_running and missing_critical:
            security_level = "LOCAL_DEVELOPMENT"
        else:
            security_level = "SECURE"
        
        return {
            "security_level": security_level,
            "running_in_aws": aws_running,
            "env_files_found": env_files,
            "env_files_count": len(env_files),
            "missing_critical_vars": missing_critical,
            "critical_vars_count": len(cls.CRITICAL_AWS_VARS),
            "available_vars_count": len(cls.CRITICAL_AWS_VARS) - len(missing_critical),
            "enforcement_active": True,
            "constitutional_compliant": len(env_files) == 0 and (not aws_running or len(missing_critical) == 0)
        }
    
    @classmethod
    def print_security_status(cls):
        """Print human-readable security status"""
        status = cls.get_environment_security_status()
        
        print("=" * 60)
        print("🔐 AWS ENVIRONMENT SECURITY STATUS")
        print("=" * 60)
        
        # Security level
        level = status["security_level"]
        if level == "SECURE":
            print("✅ SECURITY STATUS: SECURE")
        elif level == "LOCAL_DEVELOPMENT":
            print("⚠️  SECURITY STATUS: LOCAL DEVELOPMENT")
        elif level == "AWS_MISCONFIGURED":
            print("❌ SECURITY STATUS: AWS MISCONFIGURED")
        else:
            print("🚨 SECURITY STATUS: CRITICAL VIOLATION")
        
        # AWS status
        print(f"AWS Environment: {'✅ YES' if status['running_in_aws'] else '❌ NO'}")
        
        # .env files
        if status["env_files_found"]:
            print(f"❌ .env files found: {status['env_files_count']}")
            for env_file in status["env_files_found"]:
                print(f"   - {env_file}")
        else:
            print("✅ No .env files found")
        
        # Critical variables
        available = status["available_vars_count"]
        total = status["critical_vars_count"]
        print(f"Critical variables: {available}/{total} available")
        
        if status["missing_critical_vars"]:
            print("❌ Missing critical variables:")
            for var in status["missing_critical_vars"]:
                print(f"   - {var}")
        
        # Constitutional compliance
        compliant = status["constitutional_compliant"]
        print(f"Constitutional compliance: {'✅ YES' if compliant else '❌ NO'}")
        
        if not compliant:
            print("\n🔧 To achieve compliance:")
            if status["env_files_found"]:
                print("1. Delete all .env files")
            if status["missing_critical_vars"] and status["running_in_aws"]:
                print("2. Add missing variables to AWS ECS task definition")
            if not status["running_in_aws"]:
                print("3. Deploy to AWS ECS for production use")
        
        print("=" * 60)

def main():
    """Command line interface for AWS environment enforcement"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "enforce":
            AWSEnvironmentEnforcer.enforce_aws_only()
            print("✅ AWS enforcement check completed")
            
        elif command == "status":
            AWSEnvironmentEnforcer.print_security_status()
            
        elif command == "validate":
            try:
                AWSEnvironmentEnforcer.validate_critical_vars_from_aws()
                print("✅ Critical variables validation passed")
            except EnvironmentError as e:
                print(f"❌ Validation failed: {e}")
                sys.exit(1)
                
        else:
            print(f"Unknown command: {command}")
            print("Usage: python aws_env_enforcement.py [enforce|status|validate]")
            sys.exit(1)
    else:
        # Default: run full enforcement
        AWSEnvironmentEnforcer.enforce_aws_only()
        AWSEnvironmentEnforcer.print_security_status()

if __name__ == "__main__":
    main()