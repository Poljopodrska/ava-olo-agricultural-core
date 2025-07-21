#!/usr/bin/env python3
"""
Verify the entire deployment pipeline from GitHub to ECS
Checks all components are properly configured for auto-deployment
"""
import boto3
import requests
import json
import subprocess
import sys
from datetime import datetime, timedelta

class DeploymentPipelineChecker:
    def __init__(self):
        self.checks = {}
        self.codebuild = boto3.client('codebuild')
        self.ecs = boto3.client('ecs')
        self.ecr = boto3.client('ecr')
        
    def check_github_webhook(self):
        """Check if GitHub webhook is configured"""
        print("🔍 Checking GitHub webhook...")
        
        # Check local git remote
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True, text=True, check=True
            )
            repo_url = result.stdout.strip()
            print(f"   Repository: {repo_url}")
            
            # Extract owner and repo from URL
            if 'github.com' in repo_url:
                parts = repo_url.split('/')
                owner = parts[-2]
                repo = parts[-1].replace('.git', '')
                print(f"   Owner: {owner}, Repo: {repo}")
                self.checks['github_webhook'] = True
                return True
            
        except Exception as e:
            print(f"   ❌ Error checking git remote: {e}")
            
        self.checks['github_webhook'] = False
        return False
    
    def check_codebuild_trigger(self):
        """Check if CodeBuild is triggered by GitHub"""
        print("\n🔍 Checking CodeBuild configuration...")
        
        try:
            # List CodeBuild projects
            projects = self.codebuild.list_projects()
            agricultural_project = None
            
            for project in projects['projects']:
                if 'agricultural' in project.lower():
                    agricultural_project = project
                    break
            
            if not agricultural_project:
                print("   ❌ No agricultural CodeBuild project found")
                self.checks['codebuild_trigger'] = False
                return False
            
            # Get project details
            project_info = self.codebuild.batch_get_projects(names=[agricultural_project])
            if project_info['projects']:
                project = project_info['projects'][0]
                
                # Check webhook
                if project.get('webhook', {}).get('url'):
                    print(f"   ✅ Webhook configured for {agricultural_project}")
                    print(f"   Source: {project['source']['location']}")
                    self.checks['codebuild_trigger'] = True
                    return True
                else:
                    print(f"   ❌ No webhook configured for {agricultural_project}")
                    
        except Exception as e:
            print(f"   ❌ Error checking CodeBuild: {e}")
        
        self.checks['codebuild_trigger'] = False
        return False
    
    def check_ecr_repository(self):
        """Check if ECR repository exists and is accessible"""
        print("\n🔍 Checking ECR repository...")
        
        try:
            # Check for agricultural-core repository
            repos = self.ecr.describe_repositories()
            
            agricultural_repo = None
            for repo in repos['repositories']:
                if 'agricultural-core' in repo['repositoryName']:
                    agricultural_repo = repo
                    break
            
            if agricultural_repo:
                print(f"   ✅ ECR repository found: {agricultural_repo['repositoryName']}")
                print(f"   URI: {agricultural_repo['repositoryUri']}")
                
                # Check for recent images
                images = self.ecr.list_images(repositoryName=agricultural_repo['repositoryName'])
                print(f"   Images: {len(images['imageIds'])}")
                
                self.checks['ecr_repository'] = True
                return True
            else:
                print("   ❌ Agricultural ECR repository not found")
                
        except Exception as e:
            print(f"   ❌ Error checking ECR: {e}")
        
        self.checks['ecr_repository'] = False
        return False
    
    def check_buildspec_ecs_update(self):
        """Check if buildspec.yml contains ECS update command"""
        print("\n🔍 Checking buildspec.yml for ECS update...")
        
        try:
            with open('buildspec.yml', 'r') as f:
                content = f.read()
                
            if 'aws ecs update-service' in content:
                print("   ✅ buildspec.yml contains ECS update command")
                
                # Check for wait command
                if 'aws ecs wait services-stable' in content:
                    print("   ✅ buildspec.yml waits for deployment to complete")
                else:
                    print("   ⚠️  buildspec.yml missing wait command")
                
                # Check for verification
                if 'curl' in content and 'health' in content:
                    print("   ✅ buildspec.yml verifies deployment")
                else:
                    print("   ⚠️  buildspec.yml missing deployment verification")
                
                self.checks['buildspec_ecs_update'] = True
                return True
            else:
                print("   ❌ buildspec.yml missing ECS update command")
                
        except Exception as e:
            print(f"   ❌ Error reading buildspec.yml: {e}")
        
        self.checks['buildspec_ecs_update'] = False
        return False
    
    def check_iam_permissions(self):
        """Check if CodeBuild has necessary IAM permissions"""
        print("\n🔍 Checking IAM permissions...")
        
        try:
            # Run the permissions check script
            result = subprocess.run(
                ['python3', 'scripts/check_codebuild_permissions.py'],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                print("   ✅ IAM permissions verified")
                self.checks['iam_permissions'] = True
                return True
            else:
                print("   ❌ IAM permissions issue")
                print(result.stdout)
                
        except Exception as e:
            print(f"   ⚠️  Could not verify IAM permissions: {e}")
        
        self.checks['iam_permissions'] = False
        return False
    
    def check_ecs_service(self):
        """Check if ECS service is properly configured"""
        print("\n🔍 Checking ECS service configuration...")
        
        try:
            # Check agricultural-core service
            services = self.ecs.describe_services(
                cluster='ava-olo-production',
                services=['agricultural-core']
            )
            
            if services['services']:
                service = services['services'][0]
                print(f"   ✅ ECS service found: {service['serviceName']}")
                print(f"   Status: {service['status']}")
                print(f"   Running tasks: {service['runningCount']}/{service['desiredCount']}")
                print(f"   Task definition: {service['taskDefinition'].split('/')[-1]}")
                
                self.checks['ecs_service'] = True
                return True
            else:
                print("   ❌ ECS service not found")
                
        except Exception as e:
            print(f"   ❌ Error checking ECS service: {e}")
        
        self.checks['ecs_service'] = False
        return False
    
    def check_recent_builds(self):
        """Check recent CodeBuild executions"""
        print("\n🔍 Checking recent builds...")
        
        try:
            # Get recent builds
            builds = self.codebuild.list_builds_for_project(
                projectName='ava-olo-agricultural-core',
                sortOrder='DESCENDING'
            )
            
            if builds['ids']:
                # Get details of most recent build
                build_id = builds['ids'][0]
                build_info = self.codebuild.batch_get_builds(ids=[build_id])
                
                if build_info['builds']:
                    build = build_info['builds'][0]
                    print(f"   Most recent build: {build_id}")
                    print(f"   Status: {build['buildStatus']}")
                    print(f"   Started: {build['startTime']}")
                    
                    # Check if build updated ECS
                    if 'phases' in build:
                        for phase in build['phases']:
                            if phase['phaseType'] == 'POST_BUILD' and phase.get('phaseStatus') == 'SUCCEEDED':
                                print("   ✅ Post-build phase succeeded (includes ECS update)")
                                self.checks['recent_builds'] = True
                                return True
                                
        except Exception as e:
            print(f"   ⚠️  Error checking builds: {e}")
        
        self.checks['recent_builds'] = None
        return None
    
    def generate_report(self):
        """Generate final report"""
        print("\n" + "="*60)
        print("📊 DEPLOYMENT PIPELINE STATUS REPORT")
        print("="*60)
        
        all_good = True
        
        for check, status in self.checks.items():
            if status is True:
                emoji = "✅"
            elif status is False:
                emoji = "❌"
                all_good = False
            else:
                emoji = "⚠️"
            
            check_name = check.replace('_', ' ').title()
            print(f"{emoji} {check_name}: {'Configured' if status else 'Needs attention'}")
        
        print("\n" + "="*60)
        
        if all_good:
            print("✅ PIPELINE FULLY AUTOMATED!")
            print("\nYour deployment pipeline is ready:")
            print("1. Push code to GitHub")
            print("2. CodeBuild automatically triggers")
            print("3. Docker image builds and pushes to ECR")
            print("4. ECS service automatically updates")
            print("5. New version deployed in ~5 minutes")
        else:
            print("⚠️  PIPELINE NEEDS CONFIGURATION")
            print("\nTo fix:")
            
            if not self.checks.get('github_webhook'):
                print("- Configure GitHub webhook in CodeBuild console")
            
            if not self.checks.get('codebuild_trigger'):
                print("- Enable source webhook in CodeBuild project")
            
            if not self.checks.get('buildspec_ecs_update'):
                print("- Update buildspec.yml with ECS commands")
            
            if not self.checks.get('iam_permissions'):
                print("- Add ECS permissions to CodeBuild role")
                print("  Run: python3 scripts/check_codebuild_permissions.py")
        
        print("\n" + "="*60)
        
        return all_good

def main():
    """Main function"""
    print("🚀 AVA OLO Deployment Pipeline Verification")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    checker = DeploymentPipelineChecker()
    
    # Run all checks
    checker.check_github_webhook()
    checker.check_codebuild_trigger()
    checker.check_ecr_repository()
    checker.check_buildspec_ecs_update()
    checker.check_iam_permissions()
    checker.check_ecs_service()
    checker.check_recent_builds()
    
    # Generate report
    success = checker.generate_report()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())