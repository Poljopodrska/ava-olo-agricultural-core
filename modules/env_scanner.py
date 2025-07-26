#!/usr/bin/env python3
"""
ENV Scanner Module
Automatically scans codebase to find all required environment variables
"""

import os
import re
import ast
from pathlib import Path
from typing import Set, List

class ENVScanner:
    """Intelligent scanner to find all environment variables used in code"""
    
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.required_envs: Set[str] = set()
        self.env_usage_map = {}  # Track where each ENV is used
        
    def scan_python_files(self):
        """Scan all Python files for os.getenv() and os.environ calls"""
        python_files = list(self.root_dir.rglob("*.py"))
        
        for py_file in python_files:
            # Skip virtual env and cache directories
            if any(part in py_file.parts for part in ['venv', '__pycache__', '.git']):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find os.getenv('VAR_NAME') or os.getenv("VAR_NAME")
                getenv_pattern = r"os\.getenv\(['\"]([A-Z_][A-Z0-9_]*)['\"]"
                found_envs = re.findall(getenv_pattern, content)
                for env in found_envs:
                    self.required_envs.add(env)
                    if env not in self.env_usage_map:
                        self.env_usage_map[env] = []
                    self.env_usage_map[env].append(str(py_file))
                
                # Find os.environ['VAR_NAME'] or os.environ["VAR_NAME"]
                environ_pattern = r"os\.environ\[['\"]([A-Z_][A-Z0-9_]*)['\"]"
                found_envs = re.findall(environ_pattern, content)
                for env in found_envs:
                    self.required_envs.add(env)
                    if env not in self.env_usage_map:
                        self.env_usage_map[env] = []
                    self.env_usage_map[env].append(str(py_file))
                
                # Find os.environ.get('VAR_NAME')
                environ_get_pattern = r"os\.environ\.get\(['\"]([A-Z_][A-Z0-9_]*)['\"]"
                found_envs = re.findall(environ_get_pattern, content)
                for env in found_envs:
                    self.required_envs.add(env)
                    if env not in self.env_usage_map:
                        self.env_usage_map[env] = []
                    self.env_usage_map[env].append(str(py_file))
                
                # Find ENV.get('VAR_NAME') patterns (common in config files)
                env_get_pattern = r"ENV\.get\(['\"]([A-Z_][A-Z0-9_]*)['\"]"
                found_envs = re.findall(env_get_pattern, content)
                for env in found_envs:
                    self.required_envs.add(env)
                    if env not in self.env_usage_map:
                        self.env_usage_map[env] = []
                    self.env_usage_map[env].append(str(py_file))
                    
            except Exception as e:
                print(f"Error scanning {py_file}: {e}")
    
    def scan_docker_files(self):
        """Scan Dockerfiles and docker-compose for ENV variables"""
        docker_patterns = ["*Dockerfile*", "*docker-compose*", "*.dockerfile"]
        
        for pattern in docker_patterns:
            for docker_file in self.root_dir.rglob(pattern):
                if docker_file.is_file():
                    try:
                        with open(docker_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Find ENV VAR_NAME in Dockerfiles
                        env_pattern = r"ENV\s+([A-Z_][A-Z0-9_]*)"
                        found_envs = re.findall(env_pattern, content)
                        for env in found_envs:
                            self.required_envs.add(env)
                            if env not in self.env_usage_map:
                                self.env_usage_map[env] = []
                            self.env_usage_map[env].append(str(docker_file))
                        
                        # Find ARG VAR_NAME (build args that might be ENVs)
                        arg_pattern = r"ARG\s+([A-Z_][A-Z0-9_]*)"
                        found_envs = re.findall(arg_pattern, content)
                        for env in found_envs:
                            if env not in ['PYTHON_VERSION', 'NODE_VERSION']:  # Skip common build args
                                self.required_envs.add(env)
                                
                    except Exception:
                        pass
    
    def scan_env_files(self):
        """Scan .env.example and similar files for expected ENVs"""
        env_patterns = [".env.example", ".env.sample", ".env.template"]
        
        for pattern in env_patterns:
            for env_file in self.root_dir.rglob(pattern):
                if env_file.is_file():
                    try:
                        with open(env_file, 'r', encoding='utf-8') as f:
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith('#'):
                                    if '=' in line:
                                        env_name = line.split('=')[0].strip()
                                        if env_name and env_name.isupper():
                                            self.required_envs.add(env_name)
                    except Exception:
                        pass
    
    def get_all_required_envs(self) -> List[str]:
        """Return all found environment variables"""
        # Clear previous results
        self.required_envs.clear()
        self.env_usage_map.clear()
        
        # Scan all sources
        self.scan_python_files()
        self.scan_docker_files()
        self.scan_env_files()
        
        # Add known critical ENVs that might be in GitHub Secrets
        critical_envs = {
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'AWS_REGION',
            'DB_HOST',
            'DB_NAME', 
            'DB_USER',
            'DB_PASSWORD',
            'OPENAI_API_KEY',
            'OPENWEATHER_API_KEY',
            'TWILIO_ACCOUNT_SID',
            'TWILIO_AUTH_TOKEN',
            'TWILIO_WHATSAPP_NUMBER',
            'SECRET_KEY',
            'GITHUB_SHA',
            'GITHUB_REF',
            'BUILD_TIME'
        }
        
        # Only add critical ENVs if they're not already found
        self.required_envs.update(critical_envs)
        
        # Remove common non-critical ENVs
        exclude_envs = {'PATH', 'HOME', 'USER', 'SHELL', 'TERM', 'LANG', 'PWD'}
        self.required_envs -= exclude_envs
        
        return sorted(self.required_envs)
    
    def get_env_usage_report(self) -> dict:
        """Get detailed report of where each ENV is used"""
        return {
            'total_envs': len(self.required_envs),
            'env_list': self.get_all_required_envs(),
            'usage_map': self.env_usage_map
        }