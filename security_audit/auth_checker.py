"""
Authentication Security Checker
Scans for authentication vulnerabilities and weak implementations
"""

import os
import re
import ast
from typing import List, Dict, Any


class AuthenticationChecker:
    """Check authentication-related security issues"""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.findings = []
        
        # Patterns to check
        self.weak_hash_patterns = [
            r'hashlib\.md5',
            r'hashlib\.sha1',
            r'crypt\.crypt',
            r'base64\.b64encode.*password'
        ]
        
        self.hardcoded_cred_patterns = [
            r'password\s*=\s*["\'][\w\d\!\@\#\$\%\^\&\*\(\)]+["\']',
            r'pwd\s*=\s*["\'][\w\d\!\@\#\$\%\^\&\*\(\)]+["\']',
            r'passwd\s*=\s*["\'][\w\d\!\@\#\$\%\^\&\*\(\)]+["\']',
            r'secret\s*=\s*["\'][\w\d\-]+["\']',
            r'api_key\s*=\s*["\'][\w\d\-]+["\']',
            r'DB_PASSWORD\s*=\s*["\'][^\'\"]+["\']',
            r'AUTH_TOKEN\s*=\s*["\'][^\'\"]+["\']'
        ]
        
        self.session_issues = [
            r'session\[.*\]\s*=.*password',
            r'cookie.*password',
            r'Flask.*SECRET_KEY\s*=\s*["\'][^\'\"]+["\']'
        ]
    
    def check_all(self) -> List[Dict[str, Any]]:
        """Run all authentication checks"""
        self.findings = []
        
        # Check for hardcoded credentials
        self._check_hardcoded_credentials()
        
        # Check password hashing
        self._check_password_hashing()
        
        # Check session management
        self._check_session_security()
        
        # Check dashboard authentication
        self._check_dashboard_auth()
        
        # Check JWT implementation
        self._check_jwt_security()
        
        return self.findings
    
    def _check_hardcoded_credentials(self):
        """Scan for hardcoded passwords and secrets"""
        print("  - Scanning for hardcoded credentials...")
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip virtual environments and cache
            if 'venv' in root or '__pycache__' in root or '.git' in root:
                continue
                
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    self._scan_file_for_credentials(filepath)
    
    def _scan_file_for_credentials(self, filepath: str):
        """Scan a single file for hardcoded credentials"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check each pattern
            for pattern in self.hardcoded_cred_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Skip if it's in a comment
                    line_num = content[:match.start()].count('\n') + 1
                    lines = content.split('\n')
                    if line_num <= len(lines):
                        line = lines[line_num - 1].strip()
                        if not line.startswith('#') and not line.startswith('//'):
                            self.findings.append({
                                "severity": "CRITICAL",
                                "category": "Authentication",
                                "issue": "Hardcoded Credential",
                                "description": f"Potential hardcoded credential found",
                                "file": filepath.replace(self.project_root, ''),
                                "line": line_num,
                                "code_snippet": match.group()[:50] + "...",
                                "recommendation": "Move credentials to environment variables or AWS Secrets Manager"
                            })
        except Exception as e:
            pass
    
    def _check_password_hashing(self):
        """Check for weak password hashing"""
        print("  - Checking password hashing implementation...")
        
        weak_hashing_found = False
        proper_hashing_found = False
        
        for root, dirs, files in os.walk(self.project_root):
            if 'venv' in root or '__pycache__' in root:
                continue
                
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Check for weak hashing
                        for pattern in self.weak_hash_patterns:
                            if re.search(pattern, content):
                                weak_hashing_found = True
                                self.findings.append({
                                    "severity": "HIGH",
                                    "category": "Authentication",
                                    "issue": "Weak Password Hashing",
                                    "description": "Weak hashing algorithm detected (MD5/SHA1)",
                                    "file": filepath.replace(self.project_root, ''),
                                    "recommendation": "Use bcrypt, scrypt, or Argon2 for password hashing"
                                })
                        
                        # Check for proper hashing
                        if re.search(r'bcrypt|argon2|scrypt|pbkdf2', content, re.IGNORECASE):
                            proper_hashing_found = True
                    
                    except Exception:
                        pass
        
        if not proper_hashing_found and not weak_hashing_found:
            self.findings.append({
                "severity": "HIGH",
                "category": "Authentication",
                "issue": "No Password Hashing Found",
                "description": "No password hashing implementation detected",
                "recommendation": "Implement proper password hashing using bcrypt or Argon2"
            })
    
    def _check_session_security(self):
        """Check session management security"""
        print("  - Checking session management...")
        
        for root, dirs, files in os.walk(self.project_root):
            if 'venv' in root or '__pycache__' in root:
                continue
                
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Check for session issues
                        for pattern in self.session_issues:
                            matches = re.finditer(pattern, content)
                            for match in matches:
                                line_num = content[:match.start()].count('\n') + 1
                                self.findings.append({
                                    "severity": "HIGH",
                                    "category": "Authentication",
                                    "issue": "Session Security Issue",
                                    "description": "Potential sensitive data in session/cookie",
                                    "file": filepath.replace(self.project_root, ''),
                                    "line": line_num,
                                    "recommendation": "Never store passwords or sensitive data in sessions"
                                })
                    except Exception:
                        pass
    
    def _check_dashboard_auth(self):
        """Check if dashboards have authentication"""
        print("  - Checking dashboard authentication...")
        
        dashboard_files = [
            'agricultural_core_constitutional.py',
            'monitoring_api_constitutional.py',
            'services/business_dashboard.py'
        ]
        
        for dashboard_file in dashboard_files:
            filepath = os.path.join(self.project_root, dashboard_file)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check for authentication decorators or middleware
                    has_auth = any([
                        re.search(r'@.*auth.*required', content, re.IGNORECASE),
                        re.search(r'check.*auth', content, re.IGNORECASE),
                        re.search(r'login_required', content, re.IGNORECASE),
                        re.search(r'authenticate', content, re.IGNORECASE)
                    ])
                    
                    if not has_auth:
                        self.findings.append({
                            "severity": "CRITICAL",
                            "category": "Authentication",
                            "issue": "Unprotected Dashboard",
                            "description": f"Dashboard lacks authentication: {dashboard_file}",
                            "file": dashboard_file,
                            "recommendation": "Add authentication middleware to protect dashboard access"
                        })
                except Exception:
                    pass
    
    def _check_jwt_security(self):
        """Check JWT implementation if used"""
        print("  - Checking JWT security...")
        
        jwt_issues = []
        
        for root, dirs, files in os.walk(self.project_root):
            if 'venv' in root or '__pycache__' in root:
                continue
                
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Check for JWT usage
                        if 'jwt' in content.lower():
                            # Check for weak secret
                            if re.search(r'jwt.*secret.*=.*["\']secret["\']', content, re.IGNORECASE):
                                self.findings.append({
                                    "severity": "CRITICAL",
                                    "category": "Authentication",
                                    "issue": "Weak JWT Secret",
                                    "description": "JWT using weak or default secret",
                                    "file": filepath.replace(self.project_root, ''),
                                    "recommendation": "Use strong, random JWT secret from environment"
                                })
                            
                            # Check for algorithm issues
                            if re.search(r'algorithm.*=.*["\']none["\']', content, re.IGNORECASE):
                                self.findings.append({
                                    "severity": "CRITICAL",
                                    "category": "Authentication",
                                    "issue": "JWT Algorithm None",
                                    "description": "JWT using 'none' algorithm (no signature)",
                                    "file": filepath.replace(self.project_root, ''),
                                    "recommendation": "Use HS256 or RS256 algorithm for JWT"
                                })
                    except Exception:
                        pass