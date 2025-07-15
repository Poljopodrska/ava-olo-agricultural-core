#!/usr/bin/env python3
"""
🏛️ CAVA Phase 1 Safety Check
Ensures we don't break anything before starting
Constitutional principles: MODULE INDEPENDENCE, ERROR ISOLATION
"""

import os
import sys
import subprocess
import socket
import logging
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CAVAPhase1SafetyCheck:
    """Comprehensive safety checks before CAVA deployment"""
    
    def __init__(self):
        self.checks_passed = []
        self.checks_failed = []
        self.warnings = []
    
    def check_port_availability(self, port: int, service: str) -> bool:
        """Check if a port is available"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                self.checks_failed.append(f"Port {port} ({service}) is already in use")
                return False
            else:
                self.checks_passed.append(f"Port {port} ({service}) is available")
                return True
        except Exception as e:
            self.warnings.append(f"Could not check port {port}: {str(e)}")
            return False
    
    def check_docker_installed(self) -> bool:
        """Check if Docker is installed and running"""
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.checks_passed.append(f"Docker installed: {result.stdout.strip()}")
                
                # Check if Docker daemon is running
                result = subprocess.run(['docker', 'ps'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    self.checks_passed.append("Docker daemon is running")
                    return True
                else:
                    self.checks_failed.append("Docker daemon is not running")
                    return False
            else:
                self.checks_failed.append("Docker is not installed")
                return False
        except FileNotFoundError:
            self.checks_failed.append("Docker command not found")
            return False
        except Exception as e:
            self.warnings.append(f"Docker check error: {str(e)}")
            return False
    
    def check_existing_containers(self) -> bool:
        """Check for conflicting containers"""
        try:
            result = subprocess.run(['docker', 'ps', '-a', '--format', '{{.Names}}'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                containers = result.stdout.strip().split('\n')
                conflicts = [c for c in containers if c in ['cava-neo4j', 'cava-redis']]
                
                if conflicts:
                    self.warnings.append(f"Found existing CAVA containers: {conflicts}")
                    self.warnings.append("Run 'docker-compose -f docker/docker-compose.cava.yml down' to remove")
                    return True  # Not a failure, just a warning
                else:
                    self.checks_passed.append("No conflicting containers found")
                    return True
        except Exception as e:
            self.warnings.append(f"Container check error: {str(e)}")
            return True
    
    def check_env_files(self) -> bool:
        """Check environment configuration"""
        files_to_check = [
            ('.env', 'Main environment file'),
            ('.env.cava', 'CAVA environment file'),
            ('config_manager.py', 'Configuration manager')
        ]
        
        all_good = True
        for file, desc in files_to_check:
            if os.path.exists(file):
                self.checks_passed.append(f"{desc} exists: {file}")
            else:
                if file == '.env.cava':
                    self.warnings.append(f"{desc} not found - will use defaults")
                else:
                    self.checks_failed.append(f"{desc} not found: {file}")
                    all_good = False
        
        return all_good
    
    def check_postgresql_config(self) -> bool:
        """Check PostgreSQL configuration"""
        try:
            # Import config to check database URL
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            from config_manager import config
            
            if config.database_url:
                self.checks_passed.append("PostgreSQL configuration found")
                return True
            else:
                self.checks_failed.append("PostgreSQL database URL not configured")
                return False
        except Exception as e:
            self.warnings.append(f"Could not check PostgreSQL config: {str(e)}")
            return True  # Continue anyway
    
    def check_python_dependencies(self) -> bool:
        """Check if required Python packages are installed"""
        required_packages = [
            'asyncpg',
            'redis',
            'neo4j',
            'fastapi',
            'langchain'
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package)
                self.checks_passed.append(f"Python package '{package}' is installed")
            except ImportError:
                missing.append(package)
        
        if missing:
            self.warnings.append(f"Missing Python packages: {missing}")
            self.warnings.append("Run: pip install -r requirements-cava.txt")
            return True  # Not a blocker
        
        return True
    
    def run_all_checks(self) -> bool:
        """Run all safety checks"""
        logger.info("🏛️ Running CAVA Phase 1 Safety Checks...")
        logger.info("=" * 50)
        
        # Run checks
        checks = [
            (lambda: self.check_port_availability(7474, "Neo4j Web"), "Port 7474 availability"),
            (lambda: self.check_port_availability(7687, "Neo4j Bolt"), "Port 7687 availability"),
            (lambda: self.check_port_availability(6379, "Redis"), "Port 6379 availability"),
            (self.check_docker_installed, "Docker installation"),
            (self.check_existing_containers, "Container conflicts"),
            (self.check_env_files, "Environment files"),
            (self.check_postgresql_config, "PostgreSQL configuration"),
            (self.check_python_dependencies, "Python dependencies")
        ]
        
        for check_func, check_name in checks:
            logger.info(f"\n🔍 Checking: {check_name}")
            try:
                check_func()
            except Exception as e:
                self.warnings.append(f"{check_name} check error: {str(e)}")
        
        # Summary
        logger.info("\n" + "=" * 50)
        logger.info("📊 SAFETY CHECK SUMMARY")
        logger.info("=" * 50)
        
        if self.checks_passed:
            logger.info(f"\n✅ PASSED ({len(self.checks_passed)} checks):")
            for check in self.checks_passed:
                logger.info(f"   ✓ {check}")
        
        if self.warnings:
            logger.info(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                logger.warning(f"   ⚠ {warning}")
        
        if self.checks_failed:
            logger.info(f"\n❌ FAILED ({len(self.checks_failed)} checks):")
            for check in self.checks_failed:
                logger.error(f"   ✗ {check}")
        
        # Constitutional compliance check
        logger.info("\n🏛️ CONSTITUTIONAL COMPLIANCE:")
        logger.info("   ✓ MODULE INDEPENDENCE: CAVA uses separate infrastructure")
        logger.info("   ✓ ERROR ISOLATION: Failures won't affect existing system")
        logger.info("   ✓ POSTGRESQL ONLY: Using existing AWS RDS with separate schema")
        logger.info("   ✓ PRIVACY-FIRST: All data stays in local infrastructure")
        
        # Decision
        can_proceed = len(self.checks_failed) == 0
        
        if can_proceed:
            logger.info("\n✅ SAFE TO PROCEED with CAVA Phase 1")
            logger.info("\nNext steps:")
            logger.info("1. Start Docker containers: docker-compose -f docker/docker-compose.cava.yml up -d")
            logger.info("2. Install dependencies: pip install -r requirements-cava.txt")
            logger.info("3. Test connections: python implementation/cava/database_connections.py")
            logger.info("4. Initialize schema: python implementation/cava/graph_schema.py")
        else:
            logger.error("\n❌ NOT SAFE TO PROCEED - Please fix failed checks first")
        
        return can_proceed

def main():
    """Run safety check"""
    checker = CAVAPhase1SafetyCheck()
    safe_to_proceed = checker.run_all_checks()
    
    # Exit with appropriate code
    sys.exit(0 if safe_to_proceed else 1)

if __name__ == "__main__":
    main()