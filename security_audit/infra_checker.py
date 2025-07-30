"""
Infrastructure Security Checker
Scans AWS infrastructure and deployment configurations
"""

import os
import re
import json
import subprocess
from typing import List, Dict, Any


class InfrastructureChecker:
    """Check AWS infrastructure security issues"""
    
    def __init__(self):
        self.findings = []
        self.project_root = "/mnt/c/Users/HP/ava_olo_project"
    
    def check_all(self) -> List[Dict[str, Any]]:
        """Run all infrastructure security checks"""
        self.findings = []
        
        # Check ECS security
        self._check_ecs_security()
        
        # Check ALB security
        self._check_alb_security()
        
        # Check RDS security
        self._check_rds_security()
        
        # Check IAM permissions
        self._check_iam_security()
        
        # Check Docker security
        self._check_docker_security()
        
        # Check environment files
        self._check_env_files()
        
        # Check CI/CD security
        self._check_cicd_security()
        
        return self.findings
    
    def _check_ecs_security(self):
        """Check ECS service security configurations"""
        print("  - Checking ECS security...")
        
        # Check task definitions
        task_def_files = []
        for root, dirs, files in os.walk(self.project_root):
            if '.git' in root:
                continue
            for file in files:
                if 'task-definition' in file and file.endswith('.json'):
                    task_def_files.append(os.path.join(root, file))
        
        if not task_def_files:
            self.findings.append({
                "severity": "MEDIUM",
                "category": "Infrastructure",
                "issue": "No ECS Task Definitions Found",
                "description": "Could not find ECS task definition files to audit",
                "recommendation": "Ensure task definitions are version controlled"
            })
        
        for task_def_file in task_def_files:
            try:
                with open(task_def_file, 'r') as f:
                    task_def = json.load(f)
                
                # Check for privileged mode
                for container in task_def.get('containerDefinitions', []):
                    if container.get('privileged', False):
                        self.findings.append({
                            "severity": "HIGH",
                            "category": "Infrastructure",
                            "issue": "Privileged Container",
                            "description": f"Container running in privileged mode: {container.get('name')}",
                            "file": task_def_file.replace(self.project_root, ''),
                            "recommendation": "Disable privileged mode unless absolutely necessary"
                        })
                    
                    # Check for root user
                    if container.get('user') == 'root' or not container.get('user'):
                        self.findings.append({
                            "severity": "MEDIUM",
                            "category": "Infrastructure",
                            "issue": "Container Running as Root",
                            "description": f"Container may be running as root: {container.get('name')}",
                            "file": task_def_file.replace(self.project_root, ''),
                            "recommendation": "Run containers as non-root user"
                        })
                    
                    # Check for environment variables with secrets
                    for env_var in container.get('environment', []):
                        if any(secret in env_var.get('name', '').lower() for secret in ['password', 'secret', 'key', 'token']):
                            if 'value' in env_var:
                                self.findings.append({
                                    "severity": "CRITICAL",
                                    "category": "Infrastructure",
                                    "issue": "Secret in Environment Variable",
                                    "description": f"Potential secret in plain text: {env_var['name']}",
                                    "file": task_def_file.replace(self.project_root, ''),
                                    "recommendation": "Use AWS Secrets Manager or Parameter Store"
                                })
            except Exception:
                pass
    
    def _check_alb_security(self):
        """Check ALB security settings"""
        print("  - Checking ALB security...")
        
        # Check for HTTP listeners (should redirect to HTTPS)
        self.findings.append({
            "severity": "HIGH",
            "category": "Infrastructure",
            "issue": "ALB HTTP to HTTPS Redirect",
            "description": "Ensure ALB has HTTP to HTTPS redirect configured",
            "recommendation": "Configure ALB listener rules to redirect HTTP (80) to HTTPS (443)"
        })
        
        # Check for security headers
        self.findings.append({
            "severity": "MEDIUM",
            "category": "Infrastructure",
            "issue": "Missing Security Headers",
            "description": "ALB should add security headers to responses",
            "recommendation": "Configure ALB to add headers: Strict-Transport-Security, X-Content-Type-Options, X-Frame-Options"
        })
    
    def _check_rds_security(self):
        """Check RDS security configurations"""
        print("  - Checking RDS security...")
        
        # Check for database configuration files
        db_config_found = False
        for root, dirs, files in os.walk(self.project_root):
            if '.git' in root or 'venv' in root:
                continue
            for file in files:
                if file.endswith('.py') and ('config' in file or 'database' in file):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r') as f:
                            content = f.read()
                        if 'rds.amazonaws.com' in content:
                            db_config_found = True
                            
                            # Check for encryption in transit
                            if 'sslmode' not in content and 'ssl' not in content:
                                self.findings.append({
                                    "severity": "HIGH",
                                    "category": "Infrastructure",
                                    "issue": "RDS Connection Not Encrypted",
                                    "description": "Database connections should use SSL/TLS",
                                    "file": filepath.replace(self.project_root, ''),
                                    "recommendation": "Add sslmode=require to connection string"
                                })
                    except Exception:
                        pass
        
        # General RDS recommendations
        self.findings.extend([
            {
                "severity": "MEDIUM",
                "category": "Infrastructure",
                "issue": "RDS Backup Verification",
                "description": "Ensure automated backups are enabled for RDS",
                "recommendation": "Enable automated backups with 7+ day retention"
            },
            {
                "severity": "MEDIUM",
                "category": "Infrastructure",
                "issue": "RDS Encryption at Rest",
                "description": "Verify RDS instance has encryption at rest enabled",
                "recommendation": "Enable RDS encryption for data at rest"
            }
        ])
    
    def _check_iam_security(self):
        """Check IAM security best practices"""
        print("  - Checking IAM security...")
        
        # Check for IAM policy files
        iam_files = []
        for root, dirs, files in os.walk(self.project_root):
            if '.git' in root:
                continue
            for file in files:
                if 'iam' in file.lower() or 'policy' in file.lower():
                    if file.endswith(('.json', '.yml', '.yaml')):
                        iam_files.append(os.path.join(root, file))
        
        for iam_file in iam_files:
            try:
                with open(iam_file, 'r') as f:
                    content = f.read()
                
                # Check for overly permissive policies
                if '"*"' in content and 'Resource' in content:
                    self.findings.append({
                        "severity": "HIGH",
                        "category": "Infrastructure",
                        "issue": "Overly Permissive IAM Policy",
                        "description": "IAM policy with wildcard (*) permissions",
                        "file": iam_file.replace(self.project_root, ''),
                        "recommendation": "Follow principle of least privilege"
                    })
            except Exception:
                pass
        
        # General IAM recommendations
        self.findings.append({
            "severity": "MEDIUM",
            "category": "Infrastructure",
            "issue": "IAM Rotation Policy",
            "description": "Ensure IAM credentials are rotated regularly",
            "recommendation": "Implement 90-day rotation policy for IAM access keys"
        })
    
    def _check_docker_security(self):
        """Check Docker security configurations"""
        print("  - Checking Docker security...")
        
        # Check Dockerfiles
        dockerfiles = []
        for root, dirs, files in os.walk(self.project_root):
            if '.git' in root:
                continue
            for file in files:
                if file == 'Dockerfile' or file.endswith('.dockerfile'):
                    dockerfiles.append(os.path.join(root, file))
        
        for dockerfile in dockerfiles:
            try:
                with open(dockerfile, 'r') as f:
                    content = f.read()
                
                # Check for root user
                if 'USER' not in content:
                    self.findings.append({
                        "severity": "MEDIUM",
                        "category": "Infrastructure",
                        "issue": "Docker Container Running as Root",
                        "description": "Dockerfile doesn't specify non-root USER",
                        "file": dockerfile.replace(self.project_root, ''),
                        "recommendation": "Add 'USER appuser' to Dockerfile"
                    })
                
                # Check for latest tag
                if ':latest' in content or re.search(r'FROM\s+\w+\s*$', content, re.MULTILINE):
                    self.findings.append({
                        "severity": "MEDIUM",
                        "category": "Infrastructure",
                        "issue": "Docker Using Latest Tag",
                        "description": "Using 'latest' tag or untagged base image",
                        "file": dockerfile.replace(self.project_root, ''),
                        "recommendation": "Pin Docker base images to specific versions"
                    })
                
                # Check for COPY of sensitive files
                if re.search(r'COPY.*\.env', content) or re.search(r'ADD.*\.env', content):
                    self.findings.append({
                        "severity": "HIGH",
                        "category": "Infrastructure",
                        "issue": "Sensitive Files in Docker Image",
                        "description": "Copying .env or sensitive files into Docker image",
                        "file": dockerfile.replace(self.project_root, ''),
                        "recommendation": "Use Docker secrets or environment variables at runtime"
                    })
            except Exception:
                pass
    
    def _check_env_files(self):
        """Check for exposed environment files"""
        print("  - Checking environment files...")
        
        # Check for .env files
        for root, dirs, files in os.walk(self.project_root):
            if '.git' in root or 'venv' in root:
                continue
            
            for file in files:
                if file.startswith('.env'):
                    filepath = os.path.join(root, file)
                    
                    # Check if it's in .gitignore
                    gitignore_path = os.path.join(self.project_root, '.gitignore')
                    env_ignored = False
                    
                    if os.path.exists(gitignore_path):
                        with open(gitignore_path, 'r') as f:
                            gitignore_content = f.read()
                        if '.env' in gitignore_content or file in gitignore_content:
                            env_ignored = True
                    
                    if not env_ignored:
                        self.findings.append({
                            "severity": "CRITICAL",
                            "category": "Infrastructure",
                            "issue": "Environment File Not Ignored",
                            "description": f"Environment file may be committed to git: {file}",
                            "file": filepath.replace(self.project_root, ''),
                            "recommendation": "Add .env files to .gitignore"
                        })
                    
                    # Check for sensitive content
                    try:
                        with open(filepath, 'r') as f:
                            env_content = f.read()
                        
                        # Check for weak/default values
                        if 'SECRET_KEY=secret' in env_content or 'PASSWORD=password' in env_content:
                            self.findings.append({
                                "severity": "CRITICAL",
                                "category": "Infrastructure",
                                "issue": "Default Credentials in Environment",
                                "description": "Default or weak credentials found in environment file",
                                "file": filepath.replace(self.project_root, ''),
                                "recommendation": "Use strong, unique credentials"
                            })
                    except Exception:
                        pass
    
    def _check_cicd_security(self):
        """Check CI/CD pipeline security"""
        print("  - Checking CI/CD security...")
        
        # Check GitHub Actions workflows
        workflow_dir = os.path.join(self.project_root, '.github', 'workflows')
        if os.path.exists(workflow_dir):
            for file in os.listdir(workflow_dir):
                if file.endswith(('.yml', '.yaml')):
                    filepath = os.path.join(workflow_dir, file)
                    try:
                        with open(filepath, 'r') as f:
                            content = f.read()
                        
                        # Check for hardcoded secrets
                        if re.search(r'AWS_.*=.*["\'][\w\d/+=]+["\']', content):
                            self.findings.append({
                                "severity": "CRITICAL",
                                "category": "Infrastructure",
                                "issue": "Hardcoded Secrets in CI/CD",
                                "description": "Potential hardcoded AWS credentials in workflow",
                                "file": filepath.replace(self.project_root, ''),
                                "recommendation": "Use GitHub Secrets for sensitive values"
                            })
                        
                        # Check for checkout without persist-credentials
                        if 'actions/checkout' in content and 'persist-credentials: false' not in content:
                            self.findings.append({
                                "severity": "LOW",
                                "category": "Infrastructure",
                                "issue": "GitHub Token Persistence",
                                "description": "Checkout action may persist credentials",
                                "file": filepath.replace(self.project_root, ''),
                                "recommendation": "Add 'persist-credentials: false' to checkout action"
                            })
                    except Exception:
                        pass
        
        # General CI/CD recommendations
        self.findings.append({
            "severity": "MEDIUM",
            "category": "Infrastructure",
            "issue": "CI/CD Security Scanning",
            "description": "Implement security scanning in CI/CD pipeline",
            "recommendation": "Add SAST, dependency scanning, and container scanning to pipeline"
        })