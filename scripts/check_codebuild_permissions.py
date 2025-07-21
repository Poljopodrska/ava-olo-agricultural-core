#!/usr/bin/env python3
"""
Check and fix CodeBuild IAM permissions for ECS deployments
Ensures CodeBuild can update ECS services after pushing to ECR
"""
import boto3
import json
import sys
from botocore.exceptions import ClientError

def get_codebuild_role_name():
    """Find the CodeBuild role name"""
    iam = boto3.client('iam')
    
    # Common patterns for CodeBuild roles
    role_patterns = [
        'codebuild-ava-olo-agricultural-core-service-role',
        'ava-codebuild-role',
        'CodeBuildServiceRole',
        'ava-olo-codebuild-service-role'
    ]
    
    try:
        # List all roles and find CodeBuild role
        paginator = iam.get_paginator('list_roles')
        for page in paginator.paginate():
            for role in page['Roles']:
                role_name = role['RoleName']
                if any(pattern in role_name for pattern in role_patterns):
                    print(f"Found CodeBuild role: {role_name}")
                    return role_name
    except Exception as e:
        print(f"Error listing roles: {e}")
    
    return None

def check_ecs_permissions(role_name):
    """Check if role has required ECS permissions"""
    iam = boto3.client('iam')
    
    required_actions = [
        "ecs:UpdateService",
        "ecs:DescribeServices", 
        "ecs:ListServices",
        "ecs:RegisterTaskDefinition",
        "ecs:DescribeTaskDefinition"
    ]
    
    try:
        # Get all policies attached to role
        attached_policies = iam.list_attached_role_policies(RoleName=role_name)
        inline_policies = iam.list_role_policies(RoleName=role_name)
        
        print(f"\nChecking permissions for role: {role_name}")
        print(f"Attached policies: {len(attached_policies['AttachedPolicies'])}")
        print(f"Inline policies: {len(inline_policies['PolicyNames'])}")
        
        # Check for specific ECS permissions
        has_ecs_permissions = False
        
        # Check inline policies
        for policy_name in inline_policies['PolicyNames']:
            policy = iam.get_role_policy(RoleName=role_name, PolicyName=policy_name)
            policy_doc = policy['PolicyDocument']
            
            # Check if policy has ECS permissions
            for statement in policy_doc.get('Statement', []):
                actions = statement.get('Action', [])
                if isinstance(actions, str):
                    actions = [actions]
                
                if any('ecs:UpdateService' in action for action in actions):
                    has_ecs_permissions = True
                    print(f"✅ Found ECS permissions in policy: {policy_name}")
                    break
        
        return has_ecs_permissions
        
    except Exception as e:
        print(f"Error checking permissions: {e}")
        return False

def add_ecs_permissions(role_name):
    """Add ECS update permissions to CodeBuild role"""
    iam = boto3.client('iam')
    
    # Policy document for ECS updates
    ecs_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "ecs:UpdateService",
                    "ecs:DescribeServices",
                    "ecs:ListServices",
                    "ecs:RegisterTaskDefinition",
                    "ecs:DescribeTaskDefinition",
                    "ecs:ListTaskDefinitions",
                    "ecs:DeregisterTaskDefinition"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "iam:PassRole"
                ],
                "Resource": [
                    "arn:aws:iam::*:role/ecsTaskExecutionRole",
                    "arn:aws:iam::*:role/ava-*"
                ]
            }
        ]
    }
    
    try:
        # Add inline policy
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName='ECSDeploymentPolicy',
            PolicyDocument=json.dumps(ecs_policy)
        )
        print(f"✅ Successfully added ECS deployment permissions to {role_name}")
        return True
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            print(f"❌ Role {role_name} not found")
        else:
            print(f"❌ Error adding permissions: {e}")
        return False

def verify_codebuild_projects():
    """Verify CodeBuild projects exist and are configured"""
    codebuild = boto3.client('codebuild')
    
    try:
        projects = codebuild.list_projects()
        agricultural_project = None
        
        for project in projects['projects']:
            if 'agricultural' in project.lower():
                agricultural_project = project
                break
        
        if agricultural_project:
            print(f"\n✅ Found CodeBuild project: {agricultural_project}")
            
            # Get project details
            project_info = codebuild.batch_get_projects(names=[agricultural_project])
            if project_info['projects']:
                project_data = project_info['projects'][0]
                print(f"   Service role: {project_data['serviceRole']}")
                print(f"   Source: {project_data['source']['type']}")
                
                # Extract role name from ARN
                role_arn = project_data['serviceRole']
                role_name = role_arn.split('/')[-1]
                return role_name
        else:
            print("❌ No agricultural CodeBuild project found")
            
    except Exception as e:
        print(f"Error checking CodeBuild projects: {e}")
    
    return None

def main():
    """Main function to check and fix permissions"""
    print("🔍 Checking CodeBuild ECS deployment permissions...\n")
    
    # Try to find role from CodeBuild project first
    role_name = verify_codebuild_projects()
    
    # If not found, search for role by patterns
    if not role_name:
        role_name = get_codebuild_role_name()
    
    if not role_name:
        print("\n❌ Could not find CodeBuild role!")
        print("\nPlease check:")
        print("1. CodeBuild project exists in AWS console")
        print("2. IAM role is properly configured")
        return 1
    
    # Check current permissions
    has_permissions = check_ecs_permissions(role_name)
    
    if has_permissions:
        print("\n✅ CodeBuild already has ECS deployment permissions!")
    else:
        print("\n⚠️  CodeBuild missing ECS deployment permissions")
        print("Adding required permissions...")
        
        if add_ecs_permissions(role_name):
            print("\n✅ Permissions added successfully!")
            print("CodeBuild can now deploy to ECS automatically")
        else:
            print("\n❌ Failed to add permissions")
            print("You may need to add them manually in IAM console")
            return 1
    
    print("\n📋 Summary:")
    print(f"- Role: {role_name}")
    print(f"- ECS Permissions: {'✅ Yes' if has_permissions else '✅ Added'}")
    print("- Auto-deployment: Ready")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())