#!/usr/bin/env python3
"""
Comprehensive ECS Auto-Deployment Debugging Script
Identifies ALL issues preventing reliable auto-deployment
"""
import boto3
import json
import subprocess
import sys
import os
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

class DeploymentDebugger:
    def __init__(self):
        self.issues = []
        self.fixes = []
        
    def log_issue(self, severity, issue, fix=None):
        """Log an issue found during debugging"""
        self.issues.append({"severity": severity, "issue": issue})
        if fix:
            self.fixes.append(fix)
        
    def debug_git_repository(self):
        """Check GitHub repository configuration"""
        print("\n1. CHECKING GITHUB REPOSITORY...")
        print("=" * 60)
        
        try:
            # Check git remote
            result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                repo_url = result.stdout.strip()
                print(f"✅ Repository URL: {repo_url}")
                
                # Check last commit
                result = subprocess.run(['git', 'log', '-1', '--oneline'], 
                                      capture_output=True, text=True)
                print(f"✅ Last commit: {result.stdout.strip()}")
                
                # Check current branch
                result = subprocess.run(['git', 'branch', '--show-current'], 
                                      capture_output=True, text=True)
                branch = result.stdout.strip()
                print(f"✅ Current branch: {branch}")
                
                if branch != 'main':
                    self.log_issue("WARNING", f"Not on main branch (on {branch})", 
                                 "Switch to main: git checkout main")
            else:
                self.log_issue("ERROR", "Cannot determine git repository", 
                             "Ensure you're in a git repository")
                
        except Exception as e:
            self.log_issue("ERROR", f"Git check failed: {e}")
    
    def debug_codebuild_projects(self):
        """Check CodeBuild projects configuration"""
        print("\n2. CHECKING CODEBUILD PROJECTS...")
        print("=" * 60)
        
        try:
            codebuild = boto3.client('codebuild', region_name='us-east-1')
            
            # List all projects
            all_projects = codebuild.list_projects()
            print(f"Total projects: {len(all_projects['projects'])}")
            
            # Find agricultural project
            agricultural_projects = [p for p in all_projects['projects'] if 'agricultural' in p.lower()]
            
            if not agricultural_projects:
                self.log_issue("CRITICAL", "No agricultural CodeBuild project found",
                             "Create CodeBuild project for agricultural-core")
                return
                
            project_name = agricultural_projects[0]
            print(f"\n✅ Found project: {project_name}")
            
            # Get project details
            project_info = codebuild.batch_get_projects(names=[project_name])
            if project_info['projects']:
                project = project_info['projects'][0]
                
                # Check source configuration
                source = project['source']
                print(f"   Source type: {source['type']}")
                print(f"   Source location: {source.get('location', 'N/A')}")
                
                # Check webhook
                webhook = project.get('webhook', {})
                if webhook and webhook.get('url'):
                    print(f"   ✅ Webhook configured")
                else:
                    self.log_issue("CRITICAL", "No webhook configured for automatic builds",
                                 f"aws codebuild create-webhook --project-name {project_name}")
                
                # Check service role
                service_role = project.get('serviceRole', '')
                if service_role:
                    role_name = service_role.split('/')[-1]
                    print(f"   Service role: {role_name}")
                    self.check_codebuild_permissions(role_name)
                
                # Check recent builds
                builds = codebuild.list_builds_for_project(
                    projectName=project_name, 
                    sortOrder='DESCENDING',
                    maxResults=5
                )
                
                print(f"\n   Recent builds: {len(builds.get('ids', []))}")
                
                if builds.get('ids'):
                    # Check last build
                    last_build_id = builds['ids'][0]
                    build_info = codebuild.batch_get_builds(ids=[last_build_id])
                    
                    if build_info['builds']:
                        build = build_info['builds'][0]
                        print(f"   Last build: {build['buildStatus']}")
                        print(f"   Started: {build['startTime']}")
                        
                        # Check if build includes ECS update
                        self.check_build_logs_for_ecs_update(build)
                        
                else:
                    self.log_issue("WARNING", "No recent builds found")
                    
        except Exception as e:
            self.log_issue("ERROR", f"CodeBuild check failed: {e}")
    
    def check_build_logs_for_ecs_update(self, build):
        """Check if build logs contain ECS update commands"""
        try:
            # Check phases for POST_BUILD
            post_build_phases = [p for p in build.get('phases', []) 
                               if p['phaseType'] == 'POST_BUILD']
            
            if not post_build_phases:
                self.log_issue("CRITICAL", "No POST_BUILD phase found")
                return
                
            # This is where we'd check CloudWatch logs for actual commands
            # For now, we'll check buildspec.yml
            
        except Exception as e:
            print(f"   ⚠️  Could not check build logs: {e}")
    
    def check_codebuild_permissions(self, role_name):
        """Check if CodeBuild role has necessary permissions"""
        try:
            iam = boto3.client('iam')
            
            # Get inline policies
            policies = iam.list_role_policies(RoleName=role_name)
            
            has_ecs_permissions = False
            
            for policy_name in policies['PolicyNames']:
                policy = iam.get_role_policy(RoleName=role_name, PolicyName=policy_name)
                policy_doc = json.dumps(policy['PolicyDocument'])
                
                if 'ecs:UpdateService' in policy_doc:
                    has_ecs_permissions = True
                    break
            
            if has_ecs_permissions:
                print(f"   ✅ ECS permissions found")
            else:
                self.log_issue("CRITICAL", f"Role {role_name} missing ECS permissions",
                             f"Run: python3 scripts/check_codebuild_permissions.py")
                
        except Exception as e:
            print(f"   ⚠️  Could not check permissions: {e}")
    
    def debug_buildspec_yml(self):
        """Check buildspec.yml configuration"""
        print("\n3. CHECKING BUILDSPEC.YML...")
        print("=" * 60)
        
        try:
            with open('buildspec.yml', 'r') as f:
                content = f.read()
            
            print("✅ buildspec.yml exists")
            
            # Check for critical commands
            checks = {
                'ECR login': 'aws ecr get-login-password',
                'Docker build': 'docker build',
                'Docker push': 'docker push',
                'ECS update': 'aws ecs update-service',
                'Force deployment': '--force-new-deployment',
                'Wait stable': 'aws ecs wait'
            }
            
            for check_name, command in checks.items():
                if command in content:
                    print(f"   ✅ {check_name}")
                else:
                    severity = "CRITICAL" if "ECS update" in check_name else "WARNING"
                    self.log_issue(severity, f"buildspec.yml missing: {check_name}",
                                 f"Add '{command}' to buildspec.yml")
            
            # Check service name
            if 'agricultural-core' in content and 'SERVICE_NAME' not in content:
                self.log_issue("ERROR", "Service name hardcoded in buildspec.yml",
                             "Use environment variable SERVICE_NAME")
                
        except FileNotFoundError:
            self.log_issue("CRITICAL", "buildspec.yml not found",
                         "Create buildspec.yml in project root")
        except Exception as e:
            self.log_issue("ERROR", f"Error reading buildspec.yml: {e}")
    
    def debug_ecs_services(self):
        """Check ECS service configuration"""
        print("\n4. CHECKING ECS SERVICES...")
        print("=" * 60)
        
        try:
            ecs = boto3.client('ecs', region_name='us-east-1')
            
            # List all services
            services = ecs.list_services(cluster='ava-olo-production')
            print(f"Total services: {len(services['serviceArns'])}")
            
            # Find agricultural service
            agricultural_services = []
            for service_arn in services['serviceArns']:
                service_name = service_arn.split('/')[-1]
                if 'agricultural' in service_name:
                    agricultural_services.append(service_name)
            
            if not agricultural_services:
                self.log_issue("CRITICAL", "No agricultural service found in ECS")
                return
            
            service_name = agricultural_services[0]
            print(f"\n✅ Found service: {service_name}")
            
            # Get service details
            response = ecs.describe_services(
                cluster='ava-olo-production',
                services=[service_name]
            )
            
            if response['services']:
                service = response['services'][0]
                
                print(f"   Status: {service['status']}")
                print(f"   Running tasks: {service['runningCount']}")
                print(f"   Desired tasks: {service['desiredCount']}")
                print(f"   Task definition: {service['taskDefinition'].split('/')[-1]}")
                
                # Check deployments
                deployments = service['deployments']
                print(f"\n   Active deployments: {len(deployments)}")
                
                for i, deployment in enumerate(deployments):
                    age = datetime.now(deployment['createdAt'].tzinfo) - deployment['createdAt']
                    print(f"   Deployment {i+1}:")
                    print(f"     Status: {deployment['status']}")
                    print(f"     Task definition: {deployment['taskDefinition'].split('/')[-1]}")
                    print(f"     Age: {age}")
                    print(f"     Running/Desired: {deployment['runningCount']}/{deployment['desiredCount']}")
                    
                if len(deployments) > 1:
                    oldest_age = datetime.now(deployments[-1]['createdAt'].tzinfo) - deployments[-1]['createdAt']
                    if oldest_age > timedelta(minutes=10):
                        self.log_issue("WARNING", f"Stuck deployment detected (age: {oldest_age})",
                                     "Check ECS events for deployment failures")
                
                # Check recent events
                print("\n   Recent events:")
                for event in service.get('events', [])[:5]:
                    print(f"     {event['createdAt']}: {event['message']}")
                    
                    # Check for failure patterns
                    if 'failed' in event['message'].lower():
                        self.log_issue("WARNING", f"Task failures detected: {event['message']}")
                        
        except Exception as e:
            self.log_issue("ERROR", f"ECS check failed: {e}")
    
    def debug_ecr_repository(self):
        """Check ECR repository"""
        print("\n5. CHECKING ECR REPOSITORY...")
        print("=" * 60)
        
        try:
            ecr = boto3.client('ecr', region_name='us-east-1')
            
            # List repositories
            repos = ecr.describe_repositories()
            
            agricultural_repo = None
            for repo in repos['repositories']:
                if 'agricultural' in repo['repositoryName']:
                    agricultural_repo = repo
                    break
            
            if agricultural_repo:
                print(f"✅ Repository found: {agricultural_repo['repositoryName']}")
                print(f"   URI: {agricultural_repo['repositoryUri']}")
                
                # Check recent images
                images = ecr.list_images(
                    repositoryName=agricultural_repo['repositoryName'],
                    maxResults=10
                )
                
                print(f"   Total images: {len(images.get('imageIds', []))}")
                
                # Check for latest tag
                latest_images = [img for img in images.get('imageIds', []) 
                               if img.get('imageTag') == 'latest']
                
                if not latest_images:
                    self.log_issue("WARNING", "No 'latest' tag found in ECR",
                                 "Ensure buildspec.yml tags image as 'latest'")
                    
            else:
                self.log_issue("CRITICAL", "No agricultural ECR repository found")
                
        except Exception as e:
            self.log_issue("ERROR", f"ECR check failed: {e}")
    
    def check_environment_variables(self):
        """Check if required environment variables are set"""
        print("\n6. CHECKING ENVIRONMENT VARIABLES...")
        print("=" * 60)
        
        try:
            ecs = boto3.client('ecs', region_name='us-east-1')
            
            # Get service
            response = ecs.describe_services(
                cluster='ava-olo-production',
                services=['agricultural-core']
            )
            
            if response['services']:
                task_def_arn = response['services'][0]['taskDefinition']
                
                # Get task definition
                task_def = ecs.describe_task_definition(taskDefinition=task_def_arn)
                
                containers = task_def['taskDefinition']['containerDefinitions']
                if containers:
                    container = containers[0]
                    env_vars = {e['name']: '***' for e in container.get('environment', [])}
                    
                    print(f"✅ Task definition: {task_def_arn.split('/')[-1]}")
                    print(f"   Environment variables: {len(env_vars)}")
                    
                    # Check critical variables
                    critical = ['DB_HOST', 'DB_PASSWORD', 'OPENAI_API_KEY', 'OPENWEATHER_API_KEY']
                    for var in critical:
                        if var in env_vars:
                            print(f"   ✅ {var}")
                        else:
                            self.log_issue("CRITICAL", f"Missing environment variable: {var}")
                            
        except Exception as e:
            print(f"⚠️  Could not check environment variables: {e}")
    
    def generate_report(self):
        """Generate final debugging report"""
        print("\n" + "=" * 60)
        print("DEPLOYMENT DEBUGGING REPORT")
        print("=" * 60)
        
        if not self.issues:
            print("\n✅ No issues found! Deployment pipeline appears healthy.")
        else:
            print(f"\n⚠️  Found {len(self.issues)} issues:\n")
            
            # Group by severity
            critical = [i for i in self.issues if i['severity'] == 'CRITICAL']
            errors = [i for i in self.issues if i['severity'] == 'ERROR']
            warnings = [i for i in self.issues if i['severity'] == 'WARNING']
            
            if critical:
                print("CRITICAL ISSUES (must fix):")
                for issue in critical:
                    print(f"  ❌ {issue['issue']}")
                print()
            
            if errors:
                print("ERRORS (should fix):")
                for issue in errors:
                    print(f"  ⚠️  {issue['issue']}")
                print()
            
            if warnings:
                print("WARNINGS (consider fixing):")
                for issue in warnings:
                    print(f"  ⚠️  {issue['issue']}")
                print()
            
            if self.fixes:
                print("\nRECOMMENDED FIXES:")
                for i, fix in enumerate(self.fixes, 1):
                    print(f"{i}. {fix}")
        
        print("\n" + "=" * 60)
        print("Run 'python3 scripts/fix_deployment_issues.py' to apply fixes")
        print("=" * 60)
        
        return len(self.issues) == 0

def main():
    """Main debugging function"""
    print("🔍 ECS AUTO-DEPLOYMENT COMPREHENSIVE DEBUG")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    debugger = DeploymentDebugger()
    
    # Run all checks
    debugger.debug_git_repository()
    debugger.debug_codebuild_projects()
    debugger.debug_buildspec_yml()
    debugger.debug_ecs_services()
    debugger.debug_ecr_repository()
    debugger.check_environment_variables()
    
    # Generate report
    success = debugger.generate_report()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())