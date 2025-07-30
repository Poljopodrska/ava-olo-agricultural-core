"""
Data Protection Security Checker
Scans for data exposure and encryption issues
"""

import os
import re
import json
from typing import List, Dict, Any


class DataProtectionChecker:
    """Check data protection and privacy issues"""
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.findings = []
        
        # Sensitive data patterns
        self.sensitive_patterns = {
            "phone_number": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "croatian_oib": r'\b\d{11}\b',  # Croatian tax number
            "credit_card": r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
            "ip_address": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        }
        
        # Log file patterns that might expose sensitive data
        self.log_patterns = [
            r'logger\.(info|debug|error).*password',
            r'print.*password',
            r'console\.log.*password',
            r'logger.*\btoken\b',
            r'logger.*\bsecret\b',
            r'logger.*\bapi[_-]?key\b'
        ]
    
    def check_all(self) -> List[Dict[str, Any]]:
        """Run all data protection checks"""
        self.findings = []
        
        # Check for sensitive data in logs
        self._check_sensitive_data_in_logs()
        
        # Check database connection encryption
        self._check_database_encryption()
        
        # Check HTTPS implementation
        self._check_https_implementation()
        
        # Check data transmission security
        self._check_data_transmission()
        
        # Check PII handling
        self._check_pii_handling()
        
        return self.findings
    
    def _check_sensitive_data_in_logs(self):
        """Check for sensitive data being logged"""
        print("  - Scanning for sensitive data in logs...")
        
        for root, dirs, files in os.walk(self.project_root):
            if 'venv' in root or '__pycache__' in root or '.git' in root:
                continue
                
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Check for logging sensitive data
                        for pattern in self.log_patterns:
                            matches = re.finditer(pattern, content, re.IGNORECASE)
                            for match in matches:
                                line_num = content[:match.start()].count('\n') + 1
                                self.findings.append({
                                    "severity": "HIGH",
                                    "category": "Data Protection",
                                    "issue": "Sensitive Data in Logs",
                                    "description": "Potential sensitive data being logged",
                                    "file": filepath.replace(self.project_root, ''),
                                    "line": line_num,
                                    "code_snippet": match.group()[:50] + "...",
                                    "recommendation": "Never log passwords, tokens, or sensitive data"
                                })
                        
                        # Check for PII in logs
                        if 'logger' in content or 'logging' in content:
                            for data_type, pattern in self.sensitive_patterns.items():
                                if re.search(pattern, content):
                                    # Check if it's being logged
                                    log_lines = [line for line in content.split('\n') if 'log' in line.lower()]
                                    for line in log_lines:
                                        if re.search(pattern, line):
                                            self.findings.append({
                                                "severity": "MEDIUM",
                                                "category": "Data Protection",
                                                "issue": "PII in Logs",
                                                "description": f"Potential {data_type} being logged",
                                                "file": filepath.replace(self.project_root, ''),
                                                "recommendation": "Mask or remove PII from logs"
                                            })
                                            break
                    except Exception:
                        pass
    
    def _check_database_encryption(self):
        """Check database connection encryption"""
        print("  - Checking database connection security...")
        
        db_config_files = []
        ssl_enabled = False
        
        for root, dirs, files in os.walk(self.project_root):
            if 'venv' in root or '__pycache__' in root:
                continue
                
            for file in files:
                if file.endswith('.py') and ('config' in file or 'database' in file):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Check for database configuration
                        if 'DATABASE_URL' in content or 'DB_HOST' in content:
                            db_config_files.append(filepath)
                            
                            # Check for SSL/TLS
                            if any(x in content for x in ['sslmode', 'ssl=true', 'SSL_MODE', 'use_ssl']):
                                ssl_enabled = True
                            
                            # Check for unencrypted connections
                            if re.search(r'postgresql://.*@.*:5432', content) and 'sslmode' not in content:
                                self.findings.append({
                                    "severity": "HIGH",
                                    "category": "Data Protection",
                                    "issue": "Unencrypted Database Connection",
                                    "description": "Database connection may not be using SSL/TLS",
                                    "file": filepath.replace(self.project_root, ''),
                                    "recommendation": "Enable SSL/TLS for database connections (sslmode=require)"
                                })
                    except Exception:
                        pass
        
        if db_config_files and not ssl_enabled:
            self.findings.append({
                "severity": "HIGH",
                "category": "Data Protection",
                "issue": "Database Encryption Not Verified",
                "description": "Could not verify if database connections use encryption",
                "recommendation": "Ensure all database connections use SSL/TLS"
            })
    
    def _check_https_implementation(self):
        """Check HTTPS implementation"""
        print("  - Checking HTTPS implementation...")
        
        # Check for HTTP vs HTTPS URLs
        http_urls_found = False
        https_redirect_found = False
        
        for root, dirs, files in os.walk(self.project_root):
            if 'venv' in root or '__pycache__' in root:
                continue
                
            for file in files:
                if file.endswith(('.py', '.js', '.html')):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Check for hardcoded HTTP URLs
                        http_matches = re.findall(r'http://[^\s\'\"]+', content)
                        for url in http_matches:
                            if 'localhost' not in url and '127.0.0.1' not in url:
                                http_urls_found = True
                                self.findings.append({
                                    "severity": "MEDIUM",
                                    "category": "Data Protection",
                                    "issue": "Insecure HTTP URL",
                                    "description": f"HTTP URL found: {url[:50]}...",
                                    "file": filepath.replace(self.project_root, ''),
                                    "recommendation": "Use HTTPS for all external URLs"
                                })
                        
                        # Check for HTTPS redirect
                        if 'redirect' in content and 'https' in content:
                            https_redirect_found = True
                    except Exception:
                        pass
        
        # Check ALB configuration
        if not https_redirect_found:
            self.findings.append({
                "severity": "HIGH",
                "category": "Data Protection",
                "issue": "No HTTPS Redirect",
                "description": "No automatic HTTP to HTTPS redirect found",
                "recommendation": "Configure ALB to redirect HTTP to HTTPS"
            })
    
    def _check_data_transmission(self):
        """Check data transmission security"""
        print("  - Checking data transmission security...")
        
        # Check for API endpoints without encryption
        api_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            if 'venv' in root or '__pycache__' in root:
                continue
                
            for file in files:
                if file.endswith('.py') and ('api' in file or 'route' in file):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Check for sensitive data endpoints
                        if re.search(r'@app\.route.*farmer|@app\.route.*user|@app\.route.*login', content):
                            api_files.append(filepath)
                            
                            # Check if response data is encrypted
                            if 'jsonify' in content and not re.search(r'encrypt|cipher|crypto', content):
                                sensitive_endpoints = re.findall(r'@app\.route\([\'\"](.*?)[\'\"]', content)
                                for endpoint in sensitive_endpoints:
                                    if any(x in endpoint for x in ['farmer', 'user', 'profile', 'data']):
                                        self.findings.append({
                                            "severity": "MEDIUM",
                                            "category": "Data Protection",
                                            "issue": "Unencrypted API Response",
                                            "description": f"Sensitive endpoint may return unencrypted data: {endpoint}",
                                            "file": filepath.replace(self.project_root, ''),
                                            "recommendation": "Ensure all sensitive data is encrypted in transit"
                                        })
                    except Exception:
                        pass
    
    def _check_pii_handling(self):
        """Check PII handling and storage"""
        print("  - Checking PII handling...")
        
        # Check database models for PII
        for root, dirs, files in os.walk(self.project_root):
            if 'venv' in root or '__pycache__' in root:
                continue
                
            for file in files:
                if file.endswith('.py') and ('model' in file or 'schema' in file):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Check for PII fields without encryption
                        pii_fields = ['phone', 'email', 'address', 'oib', 'tax_id', 'social']
                        for field in pii_fields:
                            if field in content.lower():
                                # Check if field has encryption
                                field_pattern = f'{field}.*=.*Column'
                                if re.search(field_pattern, content, re.IGNORECASE):
                                    if not re.search(r'encrypt|cipher|hash', content, re.IGNORECASE):
                                        self.findings.append({
                                            "severity": "HIGH",
                                            "category": "Data Protection",
                                            "issue": "Unencrypted PII Storage",
                                            "description": f"PII field '{field}' may be stored unencrypted",
                                            "file": filepath.replace(self.project_root, ''),
                                            "recommendation": "Encrypt PII at rest using field-level encryption"
                                        })
                    except Exception:
                        pass
        
        # Check for GDPR compliance
        gdpr_files_found = False
        for root, dirs, files in os.walk(self.project_root):
            for file in files:
                if 'gdpr' in file.lower() or 'privacy' in file.lower():
                    gdpr_files_found = True
                    break
        
        if not gdpr_files_found:
            self.findings.append({
                "severity": "MEDIUM",
                "category": "Data Protection",
                "issue": "No GDPR Documentation",
                "description": "No GDPR or privacy policy documentation found",
                "recommendation": "Implement GDPR compliance documentation and data handling procedures"
            })