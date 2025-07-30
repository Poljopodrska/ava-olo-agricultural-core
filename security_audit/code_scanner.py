"""
Code Security Scanner
Scans for common code vulnerabilities (SQL injection, XSS, etc.)
"""

import os
import re
import ast
from typing import List, Dict, Any


class CodeSecurityScanner:
    """Scan for code-level security vulnerabilities"""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.findings = []
        
        # SQL injection patterns
        self.sql_injection_patterns = [
            # String concatenation in SQL
            r'(execute|query)\s*\(\s*["\'].*%s.*["\'].*%[^,\)]+\)',
            r'(execute|query)\s*\(\s*["\'].*\+.*["\']',
            r'f["\'].*SELECT.*{.*}.*FROM',
            r'["\']SELECT.*["\'].*\+.*(?:request|params|args)',
            # Direct string formatting
            r'\.format\s*\(.*\).*(?:SELECT|INSERT|UPDATE|DELETE)',
            r'%\s*\(.*\).*(?:SELECT|INSERT|UPDATE|DELETE)'
        ]
        
        # XSS patterns
        self.xss_patterns = [
            r'\.innerHTML\s*=',
            r'document\.write\s*\(',
            r'eval\s*\(',
            r'\|safe(?:\s|$)',  # Jinja2 safe filter
            r'autoescape\s*=\s*False',
            r'render_template_string\s*\(',
            r'Markup\s*\(.*request\.',
        ]
        
        # Command injection patterns
        self.command_injection_patterns = [
            r'os\.system\s*\(',
            r'subprocess\..*shell\s*=\s*True',
            r'eval\s*\(',
            r'exec\s*\(',
            r'__import__\s*\(',
        ]
        
        # Path traversal patterns
        self.path_traversal_patterns = [
            r'open\s*\(.*request\.',
            r'open\s*\(.*\+.*request\.',
            r'os\.path\.join\s*\(.*request\.',
            r'send_file\s*\(.*request\.',
        ]
        
        # CSRF patterns
        self.csrf_patterns = [
            r'@app\.route.*methods.*POST(?!.*csrf)',
            r'WTF.*CSRF.*=\s*False',
            r'csrf_enabled\s*=\s*False',
        ]
    
    def scan_all(self) -> List[Dict[str, Any]]:
        """Run all code security scans"""
        self.findings = []
        
        # Scan for SQL injection
        self._scan_sql_injection()
        
        # Scan for XSS
        self._scan_xss()
        
        # Scan for command injection
        self._scan_command_injection()
        
        # Scan for path traversal
        self._scan_path_traversal()
        
        # Scan for CSRF
        self._scan_csrf()
        
        # Check for insecure dependencies
        self._check_dependencies()
        
        # Check for insecure random
        self._check_insecure_random()
        
        return self.findings
    
    def _scan_sql_injection(self):
        """Scan for SQL injection vulnerabilities"""
        print("  - Scanning for SQL injection vulnerabilities...")
        
        for root, dirs, files in os.walk(self.project_root):
            if 'venv' in root or '__pycache__' in root or '.git' in root:
                continue
                
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Check for SQL operations
                        if any(keyword in content for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'execute', 'query']):
                            for pattern in self.sql_injection_patterns:
                                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                                for match in matches:
                                    line_num = content[:match.start()].count('\n') + 1
                                    self.findings.append({
                                        "severity": "CRITICAL",
                                        "category": "Code Security",
                                        "issue": "Potential SQL Injection",
                                        "description": "SQL query with string concatenation or formatting",
                                        "file": filepath.replace(self.project_root, ''),
                                        "line": line_num,
                                        "code_snippet": match.group()[:80] + "...",
                                        "recommendation": "Use parameterized queries or prepared statements"
                                    })
                            
                            # Check for safe patterns
                            if 'text(' in content or 'bindparam' in content or '?' in content:
                                # Good - using parameterized queries
                                pass
                            elif re.search(r'execute.*%s.*,\s*\(', content):
                                # Good - using proper parameterization
                                pass
                    except Exception:
                        pass
    
    def _scan_xss(self):
        """Scan for XSS vulnerabilities"""
        print("  - Scanning for XSS vulnerabilities...")
        
        for root, dirs, files in os.walk(self.project_root):
            if 'venv' in root or '__pycache__' in root:
                continue
                
            for file in files:
                if file.endswith(('.py', '.html', '.js')):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        for pattern in self.xss_patterns:
                            matches = re.finditer(pattern, content, re.IGNORECASE)
                            for match in matches:
                                line_num = content[:match.start()].count('\n') + 1
                                
                                severity = "HIGH"
                                if '|safe' in match.group() or 'autoescape' in match.group():
                                    severity = "CRITICAL"
                                
                                self.findings.append({
                                    "severity": severity,
                                    "category": "Code Security",
                                    "issue": "Potential XSS Vulnerability",
                                    "description": "Unsafe HTML rendering or JavaScript execution",
                                    "file": filepath.replace(self.project_root, ''),
                                    "line": line_num,
                                    "code_snippet": match.group(),
                                    "recommendation": "Escape all user input, avoid |safe filter, use CSP headers"
                                })
                    except Exception:
                        pass
    
    def _scan_command_injection(self):
        """Scan for command injection vulnerabilities"""
        print("  - Scanning for command injection vulnerabilities...")
        
        for root, dirs, files in os.walk(self.project_root):
            if 'venv' in root or '__pycache__' in root:
                continue
                
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        for pattern in self.command_injection_patterns:
                            matches = re.finditer(pattern, content)
                            for match in matches:
                                line_num = content[:match.start()].count('\n') + 1
                                
                                # Check if user input is involved
                                lines_around = content.split('\n')[max(0, line_num-3):line_num+2]
                                context = '\n'.join(lines_around)
                                
                                if 'request' in context or 'input' in context or 'args' in context:
                                    self.findings.append({
                                        "severity": "CRITICAL",
                                        "category": "Code Security",
                                        "issue": "Potential Command Injection",
                                        "description": "Dangerous function with possible user input",
                                        "file": filepath.replace(self.project_root, ''),
                                        "line": line_num,
                                        "code_snippet": match.group(),
                                        "recommendation": "Avoid os.system(), use subprocess with shell=False"
                                    })
                    except Exception:
                        pass
    
    def _scan_path_traversal(self):
        """Scan for path traversal vulnerabilities"""
        print("  - Scanning for path traversal vulnerabilities...")
        
        for root, dirs, files in os.walk(self.project_root):
            if 'venv' in root or '__pycache__' in root:
                continue
                
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        for pattern in self.path_traversal_patterns:
                            matches = re.finditer(pattern, content)
                            for match in matches:
                                line_num = content[:match.start()].count('\n') + 1
                                self.findings.append({
                                    "severity": "HIGH",
                                    "category": "Code Security",
                                    "issue": "Potential Path Traversal",
                                    "description": "File operation with user input",
                                    "file": filepath.replace(self.project_root, ''),
                                    "line": line_num,
                                    "code_snippet": match.group(),
                                    "recommendation": "Validate and sanitize file paths, use os.path.basename()"
                                })
                    except Exception:
                        pass
    
    def _scan_csrf(self):
        """Scan for CSRF vulnerabilities"""
        print("  - Scanning for CSRF vulnerabilities...")
        
        flask_apps = []
        csrf_protection_found = False
        
        for root, dirs, files in os.walk(self.project_root):
            if 'venv' in root or '__pycache__' in root:
                continue
                
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Check if it's a Flask app
                        if 'from flask import' in content or 'import flask' in content:
                            flask_apps.append(filepath)
                            
                            # Check for CSRF protection
                            if 'flask_wtf.csrf' in content or 'CSRFProtect' in content:
                                csrf_protection_found = True
                            
                            # Check for unprotected POST routes
                            post_routes = re.findall(r'@app\.route.*methods.*POST', content)
                            if post_routes and not csrf_protection_found:
                                self.findings.append({
                                    "severity": "HIGH",
                                    "category": "Code Security",
                                    "issue": "Missing CSRF Protection",
                                    "description": "POST routes without CSRF protection",
                                    "file": filepath.replace(self.project_root, ''),
                                    "recommendation": "Implement Flask-WTF CSRFProtect"
                                })
                    except Exception:
                        pass
        
        if flask_apps and not csrf_protection_found:
            self.findings.append({
                "severity": "HIGH",
                "category": "Code Security",
                "issue": "No CSRF Protection",
                "description": "Flask application without CSRF protection",
                "recommendation": "Add Flask-WTF and enable CSRFProtect"
            })
    
    def _check_dependencies(self):
        """Check for insecure dependencies"""
        print("  - Checking dependencies...")
        
        requirements_file = os.path.join(self.project_root, 'requirements.txt')
        if os.path.exists(requirements_file):
            try:
                with open(requirements_file, 'r') as f:
                    content = f.read()
                
                # Check for known vulnerable versions
                vulnerable_packages = {
                    'flask': ['0.', '1.0.'],  # Versions below 1.1
                    'django': ['1.', '2.0', '2.1'],  # Old Django versions
                    'requests': ['2.5.', '2.6.'],  # Old requests versions
                    'pyyaml': ['3.', '4.'],  # YAML vulnerabilities
                }
                
                for package, vulnerable_versions in vulnerable_packages.items():
                    for line in content.split('\n'):
                        if package in line.lower():
                            for vuln_version in vulnerable_versions:
                                if vuln_version in line:
                                    self.findings.append({
                                        "severity": "HIGH",
                                        "category": "Code Security",
                                        "issue": "Vulnerable Dependency",
                                        "description": f"Potentially vulnerable version of {package}",
                                        "file": "requirements.txt",
                                        "recommendation": f"Update {package} to latest stable version"
                                    })
                                    break
            except Exception:
                pass
        
        # Check for missing security packages
        security_packages = ['python-dotenv', 'cryptography']
        if os.path.exists(requirements_file):
            with open(requirements_file, 'r') as f:
                requirements = f.read().lower()
            
            for package in security_packages:
                if package not in requirements:
                    self.findings.append({
                        "severity": "MEDIUM",
                        "category": "Code Security",
                        "issue": "Missing Security Package",
                        "description": f"Recommended security package '{package}' not found",
                        "recommendation": f"Consider adding {package} for better security"
                    })
    
    def _check_insecure_random(self):
        """Check for insecure random number generation"""
        print("  - Checking for insecure randomness...")
        
        for root, dirs, files in os.walk(self.project_root):
            if 'venv' in root or '__pycache__' in root:
                continue
                
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Check for insecure random
                        if 'random' in content:
                            # Check if used for security purposes
                            security_contexts = ['token', 'secret', 'password', 'key', 'salt', 'nonce']
                            for context in security_contexts:
                                if context in content.lower():
                                    if 'random.random' in content or 'random.randint' in content:
                                        if 'secrets' not in content and 'os.urandom' not in content:
                                            self.findings.append({
                                                "severity": "HIGH",
                                                "category": "Code Security",
                                                "issue": "Insecure Random Generation",
                                                "description": "Using random module for security-sensitive operations",
                                                "file": filepath.replace(self.project_root, ''),
                                                "recommendation": "Use secrets module or os.urandom() for cryptographic randomness"
                                            })
                                            break
                    except Exception:
                        pass