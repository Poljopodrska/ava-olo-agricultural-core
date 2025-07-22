#!/usr/bin/env python3
"""
EMERGENCY: Find all AWS infrastructure and working endpoints
Complete infrastructure audit to restore service
"""
import subprocess
import json
from datetime import datetime

class EmergencyInfrastructureCheck:
    def __init__(self):
        self.working_endpoints = []
        self.infrastructure = {
            'albs': [],
            'ecs_services': [],
            'app_runner': [],
            'cloudfront': [],
            'route53': []
        }
        
    def run_aws_command(self, service, command, region='us-east-1'):
        """Run AWS CLI command and return JSON output"""
        try:
            cmd = f"aws {service} {command} --region {region} --output json"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                return json.loads(result.stdout) if result.stdout else {}
            else:
                print(f"Error running command: {cmd}")
                print(f"Error: {result.stderr}")
                return {}
        except Exception as e:
            print(f"Exception running AWS command: {e}")
            return {}
    
    def check_albs(self):
        """Find ALL Application Load Balancers"""
        print("\n=== CHECKING ALL APPLICATION LOAD BALANCERS ===")
        print("=" * 60)
        
        # Get all load balancers
        response = self.run_aws_command('elbv2', 'describe-load-balancers')
        
        if not response.get('LoadBalancers'):
            print("❌ No load balancers found!")
            return
        
        for lb in response['LoadBalancers']:
            if lb['Type'] == 'application':
                alb_info = {
                    'name': lb['LoadBalancerName'],
                    'dns': lb['DNSName'],
                    'state': lb['State']['Code'],
                    'scheme': lb['Scheme'],
                    'vpc': lb.get('VpcId', 'N/A'),
                    'arn': lb['LoadBalancerArn']
                }
                
                print(f"\nALB: {alb_info['name']}")
                print(f"  DNS Name: {alb_info['dns']}")
                print(f"  State: {alb_info['state']}")
                print(f"  Type: {alb_info['scheme']}")
                print(f"  VPC: {alb_info['vpc']}")
                
                # Check if DNS is resolvable
                dns_check = subprocess.run(
                    f"nslookup {alb_info['dns']} 2>&1 | grep -q 'Address'",
                    shell=True
                )
                if dns_check.returncode == 0:
                    print(f"  DNS Status: ✅ Resolvable")
                else:
                    print(f"  DNS Status: ❌ Not resolvable")
                
                # Check target groups
                tg_response = self.run_aws_command(
                    'elbv2', 
                    f'describe-target-groups --load-balancer-arn {lb["LoadBalancerArn"]}'
                )
                
                alb_info['target_groups'] = []
                for tg in tg_response.get('TargetGroups', []):
                    tg_info = {
                        'name': tg['TargetGroupName'],
                        'port': tg.get('Port', 'N/A'),
                        'protocol': tg.get('Protocol', 'N/A')
                    }
                    
                    print(f"\n  Target Group: {tg_info['name']}")
                    print(f"    Port: {tg_info['port']}")
                    print(f"    Protocol: {tg_info['protocol']}")
                    
                    # Check target health
                    health_response = self.run_aws_command(
                        'elbv2',
                        f'describe-target-health --target-group-arn {tg["TargetGroupArn"]}'
                    )
                    
                    targets = health_response.get('TargetHealthDescriptions', [])
                    healthy = sum(1 for t in targets if t['TargetHealth']['State'] == 'healthy')
                    unhealthy = sum(1 for t in targets if t['TargetHealth']['State'] == 'unhealthy')
                    
                    print(f"    Health: {healthy} healthy, {unhealthy} unhealthy, {len(targets)} total")
                    
                    tg_info['healthy_targets'] = healthy
                    tg_info['total_targets'] = len(targets)
                    alb_info['target_groups'].append(tg_info)
                
                # Test endpoint
                print(f"\n  Testing endpoint...")
                test_url = f"http://{alb_info['dns']}/"
                test_result = subprocess.run(
                    f"curl -s -o /dev/null -w '%{{http_code}}' -m 5 {test_url}",
                    shell=True, capture_output=True, text=True
                )
                
                if test_result.stdout and test_result.stdout != '000':
                    print(f"    HTTP Status: {test_result.stdout}")
                    if test_result.stdout.startswith(('2', '3', '4')):
                        print(f"    ✅ ALB is responding!")
                        self.working_endpoints.append({
                            'type': 'ALB',
                            'name': alb_info['name'],
                            'url': test_url,
                            'status': test_result.stdout
                        })
                else:
                    print(f"    ❌ ALB not responding (timeout or error)")
                
                self.infrastructure['albs'].append(alb_info)
        
        if not self.infrastructure['albs']:
            print("\n❌ No Application Load Balancers found!")
    
    def check_ecs_services(self):
        """Check all ECS clusters and services"""
        print("\n\n=== CHECKING ECS SERVICES ===")
        print("=" * 60)
        
        # List all clusters
        clusters_response = self.run_aws_command('ecs', 'list-clusters')
        
        if not clusters_response.get('clusterArns'):
            print("❌ No ECS clusters found!")
            return
        
        for cluster_arn in clusters_response['clusterArns']:
            cluster_name = cluster_arn.split('/')[-1]
            print(f"\nCluster: {cluster_name}")
            
            # List services in cluster
            services_response = self.run_aws_command(
                'ecs',
                f'list-services --cluster {cluster_name}'
            )
            
            if not services_response.get('serviceArns'):
                print("  No services in this cluster")
                continue
            
            # Describe services
            service_details = self.run_aws_command(
                'ecs',
                f'describe-services --cluster {cluster_name} --services {" ".join(services_response["serviceArns"])}'
            )
            
            for service in service_details.get('services', []):
                service_info = {
                    'cluster': cluster_name,
                    'name': service['serviceName'],
                    'status': service['status'],
                    'running': service['runningCount'],
                    'desired': service['desiredCount'],
                    'task_definition': service['taskDefinition'].split('/')[-1]
                }
                
                print(f"\n  Service: {service_info['name']}")
                print(f"    Status: {service_info['status']}")
                print(f"    Tasks: {service_info['running']}/{service_info['desired']} running")
                print(f"    Task Definition: {service_info['task_definition']}")
                
                # Check for load balancers
                if service.get('loadBalancers'):
                    for lb in service['loadBalancers']:
                        tg_arn = lb.get('targetGroupArn', '')
                        if tg_arn:
                            tg_name = tg_arn.split('/')[-2]
                            print(f"    Target Group: {tg_name}")
                
                # Check recent events
                events = service.get('events', [])[:3]
                if events:
                    print("    Recent events:")
                    for event in events:
                        print(f"      - {event['message']}")
                
                self.infrastructure['ecs_services'].append(service_info)
    
    def check_app_runner(self):
        """Check App Runner services"""
        print("\n\n=== CHECKING APP RUNNER SERVICES ===")
        print("=" * 60)
        
        response = self.run_aws_command('apprunner', 'list-services')
        
        if not response.get('ServiceSummaryList'):
            print("No App Runner services found")
            return
        
        for service in response['ServiceSummaryList']:
            service_arn = service['ServiceArn']
            service_name = service['ServiceName']
            
            # Get service details
            details = self.run_aws_command(
                'apprunner',
                f'describe-service --service-arn {service_arn}'
            )
            
            if details.get('Service'):
                svc = details['Service']
                service_info = {
                    'name': service_name,
                    'url': svc.get('ServiceUrl', 'N/A'),
                    'status': svc.get('Status', 'N/A')
                }
                
                print(f"\nApp Runner Service: {service_name}")
                print(f"  URL: https://{service_info['url']}")
                print(f"  Status: {service_info['status']}")
                
                # Test endpoint
                if service_info['url'] != 'N/A':
                    test_url = f"https://{service_info['url']}/"
                    test_result = subprocess.run(
                        f"curl -s -o /dev/null -w '%{{http_code}}' -m 5 {test_url}",
                        shell=True, capture_output=True, text=True
                    )
                    
                    if test_result.stdout and test_result.stdout != '000':
                        print(f"  HTTP Status: {test_result.stdout}")
                        if test_result.stdout.startswith(('2', '3', '4')):
                            print(f"  ✅ Service is responding!")
                            self.working_endpoints.append({
                                'type': 'App Runner',
                                'name': service_name,
                                'url': test_url,
                                'status': test_result.stdout
                            })
                
                self.infrastructure['app_runner'].append(service_info)
    
    def check_cloudfront(self):
        """Check CloudFront distributions"""
        print("\n\n=== CHECKING CLOUDFRONT DISTRIBUTIONS ===")
        print("=" * 60)
        
        response = self.run_aws_command('cloudfront', 'list-distributions')
        
        if not response.get('DistributionList', {}).get('Items'):
            print("No CloudFront distributions found")
            return
        
        for dist in response['DistributionList']['Items']:
            dist_info = {
                'id': dist['Id'],
                'domain': dist['DomainName'],
                'status': dist['Status'],
                'enabled': dist['Enabled']
            }
            
            print(f"\nDistribution: {dist_info['id']}")
            print(f"  Domain: {dist_info['domain']}")
            print(f"  Status: {dist_info['status']}")
            print(f"  Enabled: {dist_info['enabled']}")
            
            if dist.get('Aliases', {}).get('Items'):
                print(f"  Aliases: {', '.join(dist['Aliases']['Items'])}")
            
            self.infrastructure['cloudfront'].append(dist_info)
    
    def generate_recovery_document(self):
        """Generate comprehensive recovery documentation"""
        print("\n\n=== GENERATING RECOVERY DOCUMENT ===")
        print("=" * 60)
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        doc = f"""# EMERGENCY INFRASTRUCTURE REPORT
Generated: {timestamp}

## SUMMARY
- Total ALBs found: {len(self.infrastructure['albs'])}
- Total ECS services: {len(self.infrastructure['ecs_services'])}
- Total App Runner services: {len(self.infrastructure['app_runner'])}
- Working endpoints found: {len(self.working_endpoints)}

## WORKING ENDPOINTS
"""
        
        if self.working_endpoints:
            for endpoint in self.working_endpoints:
                doc += f"\n### ✅ {endpoint['type']}: {endpoint['name']}"
                doc += f"\n- URL: {endpoint['url']}"
                doc += f"\n- Status: HTTP {endpoint['status']}\n"
        else:
            doc += "\n❌ NO WORKING ENDPOINTS FOUND!\n"
        
        doc += "\n## INFRASTRUCTURE DETAILS\n"
        
        # ALBs
        doc += "\n### Application Load Balancers\n"
        if self.infrastructure['albs']:
            for alb in self.infrastructure['albs']:
                doc += f"\n**{alb['name']}**"
                doc += f"\n- DNS: {alb['dns']}"
                doc += f"\n- State: {alb['state']}"
                doc += f"\n- Target Groups: {len(alb['target_groups'])}"
                healthy_total = sum(tg['healthy_targets'] for tg in alb['target_groups'])
                doc += f"\n- Healthy Targets: {healthy_total}\n"
        else:
            doc += "\nNo ALBs found.\n"
        
        # ECS Services
        doc += "\n### ECS Services\n"
        if self.infrastructure['ecs_services']:
            for svc in self.infrastructure['ecs_services']:
                doc += f"\n**{svc['name']}** (Cluster: {svc['cluster']})"
                doc += f"\n- Status: {svc['status']}"
                doc += f"\n- Running: {svc['running']}/{svc['desired']}"
                doc += f"\n- Task Definition: {svc['task_definition']}\n"
        else:
            doc += "\nNo ECS services found.\n"
        
        # Recovery steps
        doc += "\n## RECOVERY ACTIONS NEEDED\n"
        
        if not self.working_endpoints:
            doc += "\n### CRITICAL: No working endpoints!"
            doc += "\n1. Check if ECS tasks are actually running"
            doc += "\n2. Verify security groups allow traffic"
            doc += "\n3. Check if ALB listeners are configured"
            doc += "\n4. Verify DNS records point to correct ALBs"
        
        # Check for specific issues
        for alb in self.infrastructure['albs']:
            if alb['state'] != 'active':
                doc += f"\n\n### ALB {alb['name']} is not active!"
                doc += f"\n- Current state: {alb['state']}"
                doc += "\n- Action: Check ALB configuration in AWS console"
            
            healthy = sum(tg['healthy_targets'] for tg in alb['target_groups'])
            if healthy == 0 and alb['target_groups']:
                doc += f"\n\n### ALB {alb['name']} has no healthy targets!"
                doc += "\n- Action: Check ECS service health"
                doc += "\n- Action: Verify security groups"
                doc += "\n- Action: Check task health checks"
        
        for svc in self.infrastructure['ecs_services']:
            if svc['running'] == 0:
                doc += f"\n\n### ECS Service {svc['name']} has no running tasks!"
                doc += f"\n- Cluster: {svc['cluster']}"
                doc += "\n- Action: Check task logs for failures"
                doc += "\n- Action: Verify task definition"
                doc += "\n- Action: Check for resource constraints"
        
        # Save document
        with open('EMERGENCY_INFRASTRUCTURE_REPORT.md', 'w') as f:
            f.write(doc)
        
        print(f"\n✅ Report saved to: EMERGENCY_INFRASTRUCTURE_REPORT.md")
        
        return doc
    
    def run_full_check(self):
        """Run all infrastructure checks"""
        print("🚨 EMERGENCY INFRASTRUCTURE CHECK STARTED")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        self.check_albs()
        self.check_ecs_services()
        self.check_app_runner()
        self.check_cloudfront()
        
        # Generate and display summary
        print("\n\n" + "=" * 60)
        print("EMERGENCY CHECK COMPLETE")
        print("=" * 60)
        
        if self.working_endpoints:
            print(f"\n✅ Found {len(self.working_endpoints)} working endpoint(s):")
            for endpoint in self.working_endpoints:
                print(f"  - {endpoint['url']} (HTTP {endpoint['status']})")
        else:
            print("\n❌ CRITICAL: No working endpoints found!")
        
        # Generate recovery document
        self.generate_recovery_document()

def main():
    checker = EmergencyInfrastructureCheck()
    checker.run_full_check()

if __name__ == "__main__":
    main()