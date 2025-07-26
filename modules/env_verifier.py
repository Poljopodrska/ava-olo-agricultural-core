#!/usr/bin/env python3
"""
ENV Verifier Module
Checks if required environment variables are properly configured in AWS ECS
"""

import os
import boto3
from typing import Dict, List, Optional
from datetime import datetime

class ENVVerifier:
    """Verifies environment variables across local and AWS environments"""
    
    def __init__(self):
        try:
            self.ecs = boto3.client('ecs', region_name='us-east-1')
            self.secrets = boto3.client('secretsmanager', region_name='us-east-1')
            self.aws_available = True
        except Exception as e:
            print(f"AWS clients initialization failed: {e}")
            self.aws_available = False
    
    def check_local_env(self, env_name: str) -> Dict:
        """Check if ENV exists locally"""
        exists = env_name in os.environ
        value = os.environ.get(env_name, '')
        
        # Mask sensitive values
        masked_value = self._mask_sensitive_value(env_name, value)
        
        return {
            'name': env_name,
            'local_exists': exists,
            'local_value_preview': masked_value if exists else None,
            'local_value_length': len(value) if exists else 0
        }
    
    def _mask_sensitive_value(self, env_name: str, value: str) -> str:
        """Mask sensitive environment variable values"""
        if not value:
            return ''
            
        sensitive_patterns = ['KEY', 'SECRET', 'PASSWORD', 'TOKEN', 'PRIVATE']
        
        # Check if this is a sensitive variable
        is_sensitive = any(pattern in env_name.upper() for pattern in sensitive_patterns)
        
        if is_sensitive and len(value) > 4:
            # Show first 4 chars only for sensitive values
            return f"{value[:4]}...{len(value)-4} more chars"
        elif len(value) > 20:
            # Truncate long values
            return f"{value[:20]}..."
        else:
            return value
    
    def check_ecs_task_env(self, service_name: str, env_name: str) -> Dict:
        """Check if ENV is configured in ECS task definition"""
        if not self.aws_available:
            return {
                'configured': False,
                'source': 'aws-unavailable',
                'error': 'AWS connection not available'
            }
            
        try:
            # Get the service to find active task definition
            service_response = self.ecs.describe_services(
                cluster='ava-olo-production',
                services=[service_name]
            )
            
            if not service_response['services']:
                return {'configured': False, 'source': 'service-not-found'}
            
            task_definition_arn = service_response['services'][0]['taskDefinition']
            
            # Get task definition details
            task_def_response = self.ecs.describe_task_definition(
                taskDefinition=task_definition_arn
            )
            
            task_def = task_def_response['taskDefinition']
            
            # Check all containers in the task definition
            for container in task_def['containerDefinitions']:
                # Check environment variables
                env_vars = {e['name']: e['value'] for e in container.get('environment', [])}
                if env_name in env_vars:
                    return {
                        'configured': True,
                        'source': 'environment',
                        'container': container['name'],
                        'value_preview': self._mask_sensitive_value(env_name, env_vars[env_name])
                    }
                
                # Check secrets (from AWS Secrets Manager)
                secrets = {s['name']: s['valueFrom'] for s in container.get('secrets', [])}
                if env_name in secrets:
                    return {
                        'configured': True,
                        'source': 'secrets-manager',
                        'container': container['name'],
                        'secret_arn': secrets[env_name]
                    }
            
            return {'configured': False, 'source': 'not-found'}
            
        except Exception as e:
            return {
                'configured': False,
                'source': 'error',
                'error': str(e)
            }
    
    def verify_all_envs(self, required_envs: List[str], service_name: str) -> Dict:
        """Comprehensive ENV verification for a service"""
        results = {
            'service': service_name,
            'timestamp': datetime.utcnow().isoformat(),
            'total_required': len(required_envs),
            'local_found': 0,
            'aws_found': 0,
            'missing_local': [],
            'missing_aws': [],
            'details': {},
            'status': 'UNKNOWN'
        }
        
        for env in required_envs:
            # Check local
            local_check = self.check_local_env(env)
            if local_check['local_exists']:
                results['local_found'] += 1
            else:
                results['missing_local'].append(env)
            
            # Check AWS
            aws_check = self.check_ecs_task_env(service_name, env)
            if aws_check.get('configured'):
                results['aws_found'] += 1
            else:
                results['missing_aws'].append(env)
            
            # Store detailed results
            results['details'][env] = {
                'local': local_check,
                'aws': aws_check
            }
        
        # Determine overall status
        aws_percentage = (results['aws_found'] / results['total_required']) * 100 if results['total_required'] > 0 else 0
        
        if aws_percentage == 100:
            results['status'] = 'GREEN'
            results['status_message'] = 'All environment variables properly configured!'
        elif aws_percentage >= 80:
            results['status'] = 'YELLOW'
            results['status_message'] = f"Missing {len(results['missing_aws'])} environment variables"
        else:
            results['status'] = 'RED'
            results['status_message'] = f"CRITICAL: {len(results['missing_aws'])} environment variables missing!"
        
        results['aws_coverage_percentage'] = round(aws_percentage, 1)
        
        return results
    
    def get_critical_missing_envs(self, missing_envs: List[str]) -> List[str]:
        """Identify which missing ENVs are critical"""
        critical_patterns = [
            'DB_', 'DATABASE_',
            'AWS_', 
            'OPENAI_API_KEY',
            'SECRET_KEY',
            'API_KEY',
            'AUTH_'
        ]
        
        critical_missing = []
        for env in missing_envs:
            if any(env.startswith(pattern) for pattern in critical_patterns):
                critical_missing.append(env)
        
        return critical_missing