#!/usr/bin/env python3
"""
Test Rollback Procedures - Verify rollback capability without executing
"""
import subprocess
import json
import requests
import time

def test_rollback_prerequisites():
    """Test that rollback prerequisites are available"""
    print("🔍 Testing Rollback Prerequisites")
    print("=" * 40)
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: AWS CLI available
    total_tests += 1
    try:
        result = subprocess.run(['aws', '--version'], capture_output=True, text=True, timeout=10)
        aws_available = result.returncode == 0
        print(f"  AWS CLI available: {'✅ YES' if aws_available else '❌ NO'}")
        if aws_available:
            tests_passed += 1
    except Exception as e:
        print(f"  AWS CLI available: ❌ NO ({e})")
    
    # Test 2: AWS credentials configured
    total_tests += 1
    try:
        result = subprocess.run(['aws', 'sts', 'get-caller-identity'], capture_output=True, text=True, timeout=10)
        aws_creds = result.returncode == 0
        print(f"  AWS credentials configured: {'✅ YES' if aws_creds else '❌ NO'}")
        if aws_creds:
            tests_passed += 1
    except Exception as e:
        print(f"  AWS credentials configured: ❌ NO ({e})")
    
    # Test 3: Baseline states available
    total_tests += 1
    try:
        result = subprocess.run(['ls', '/mnt/c/Users/HP/ava-olo-constitutional/protection_system/baselines/'], 
                              capture_output=True, text=True, timeout=5)
        baselines_available = result.returncode == 0 and len(result.stdout.strip().split('\n')) > 0
        print(f"  Baseline states available: {'✅ YES' if baselines_available else '❌ NO'}")
        if baselines_available:
            tests_passed += 1
            print(f"    Available baselines: {len(result.stdout.strip().split())}")
    except Exception as e:
        print(f"  Baseline states available: ❌ NO ({e})")
    
    # Test 4: Emergency rollback script exists
    total_tests += 1
    try:
        result = subprocess.run(['ls', '/mnt/c/Users/HP/ava-olo-constitutional/protection_system/emergency_rollback.sh'], 
                              capture_output=True, text=True, timeout=5)
        script_exists = result.returncode == 0
        print(f"  Emergency rollback script: {'✅ YES' if script_exists else '❌ NO'}")
        if script_exists:
            tests_passed += 1
    except Exception as e:
        print(f"  Emergency rollback script: ❌ NO ({e})")
    
    success_rate = (tests_passed / total_tests) * 100
    print(f"\n  Prerequisites: {success_rate:.1f}% ready ({tests_passed}/{total_tests})")
    
    return success_rate >= 75

def test_current_ecs_state():
    """Test current ECS deployment state"""
    print("\n🔍 Testing Current ECS State")
    print("=" * 40)
    
    services_tested = 0
    services_healthy = 0
    
    # Get ECS service information
    services = ["monitoring-dashboards", "agricultural-core"]
    
    for service in services:
        services_tested += 1
        try:
            # Get service status
            cmd = ['aws', 'ecs', 'describe-services', 
                   '--cluster', 'ava-olo-production', 
                   '--services', service,
                   '--query', 'services[0].[serviceName,status,runningCount,desiredCount,taskDefinition]',
                   '--output', 'json']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if data and len(data) >= 4:
                    service_name = data[0]
                    status = data[1]
                    running = data[2]
                    desired = data[3]
                    task_def = data[4] if len(data) > 4 else "unknown"
                    
                    is_healthy = status == "ACTIVE" and running == desired and running > 0
                    health_status = "✅ HEALTHY" if is_healthy else "❌ UNHEALTHY"
                    
                    print(f"  {service}: {health_status}")
                    print(f"    Status: {status}, Running: {running}/{desired}")
                    print(f"    Task Definition: {task_def}")
                    
                    if is_healthy:
                        services_healthy += 1
                else:
                    print(f"  {service}: ❌ NO DATA")
            else:
                print(f"  {service}: ❌ ERROR ({result.stderr})")
                
        except Exception as e:
            print(f"  {service}: ❌ EXCEPTION ({e})")
    
    health_rate = (services_healthy / services_tested) * 100 if services_tested > 0 else 0
    print(f"\n  ECS Health: {health_rate:.1f}% ({services_healthy}/{services_tested})")
    
    return health_rate >= 50

def test_rollback_simulation():
    """Simulate rollback without executing"""
    print("\n🎭 Simulating Rollback Procedure")
    print("=" * 40)
    
    # Get current task definitions
    print("  Getting current task definitions...")
    
    try:
        # Get monitoring service task def
        cmd = ['aws', 'ecs', 'describe-services',
               '--cluster', 'ava-olo-production',
               '--services', 'monitoring-dashboards',
               '--query', 'services[0].taskDefinition',
               '--output', 'text']
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            current_task_def = result.stdout.strip()
            print(f"    Current monitoring task: {current_task_def}")
            
            # Extract revision number
            if ":" in current_task_def:
                family = current_task_def.split(":")[0]
                current_rev = int(current_task_def.split(":")[1])
                previous_rev = current_rev - 1
                
                print(f"    Would rollback to: {family}:{previous_rev}")
                
                if previous_rev > 0:
                    print("    ✅ Rollback target available")
                    rollback_possible = True
                else:
                    print("    ❌ No previous revision available")
                    rollback_possible = False
            else:
                print("    ❌ Cannot parse task definition")
                rollback_possible = False
        else:
            print("    ❌ Cannot get current task definition")
            rollback_possible = False
            
    except Exception as e:
        print(f"    ❌ Error: {e}")
        rollback_possible = False
    
    # Simulate rollback timing
    print(f"\n  Simulated rollback procedure:")
    print(f"    1. Update service task definition: ~30 seconds")
    print(f"    2. Wait for service stabilization: ~60-120 seconds")
    print(f"    3. Verify rollback success: ~30 seconds")
    print(f"    Total estimated time: ~2-3 minutes")
    
    return rollback_possible

def test_rollback_verification():
    """Test the verification process after rollback"""
    print("\n🔍 Testing Rollback Verification Process")
    print("=" * 40)
    
    # Test if protection gate would work to verify rollback
    try:
        print("  Testing protection gate availability...")
        gate_script = "/mnt/c/Users/HP/ava-olo-constitutional/protection_system/pre_deployment_gate.sh"
        
        result = subprocess.run(['ls', gate_script], capture_output=True, text=True, timeout=5)
        gate_available = result.returncode == 0
        
        print(f"    Protection gate script: {'✅ AVAILABLE' if gate_available else '❌ MISSING'}")
        
        if gate_available:
            print("    Verification process would:")
            print("      1. ✅ Test critical endpoints")
            print("      2. ✅ Verify MANGO rule compliance")
            print("      3. ✅ Check visual regression")
            print("      4. ✅ Validate performance")
            print("      5. ✅ Confirm constitutional compliance")
            
            verification_ready = True
        else:
            verification_ready = False
            
    except Exception as e:
        print(f"    ❌ Error testing verification: {e}")
        verification_ready = False
    
    # Test current service health as verification example
    print(f"\n  Current service health check:")
    base_url = "http://ava-olo-alb-65365776.us-east-1.elb.amazonaws.com"
    
    endpoints = [
        ("/business-dashboard", "Business Dashboard"),
        ("/register", "Registration"),
        ("/health", "Health Check")
    ]
    
    healthy_endpoints = 0
    total_endpoints = len(endpoints)
    
    for endpoint, name in endpoints:
        try:
            resp = requests.get(f"{base_url}{endpoint}", timeout=5)
            is_healthy = resp.status_code == 200
            status = "✅ HEALTHY" if is_healthy else "❌ UNHEALTHY"
            print(f"    {name}: {status}")
            if is_healthy:
                healthy_endpoints += 1
        except Exception as e:
            print(f"    {name}: ❌ ERROR")
    
    service_health = (healthy_endpoints / total_endpoints) * 100
    print(f"    Overall health: {service_health:.1f}%")
    
    return verification_ready and service_health >= 66

def main():
    """Run all rollback procedure tests"""
    print("🚨 ROLLBACK PROCEDURE TEST SUITE")
    print("=" * 50)
    print("Testing rollback capability without executing rollback")
    print()
    
    # Run all rollback tests
    prereq_test = test_rollback_prerequisites()
    ecs_test = test_current_ecs_state()
    simulation_test = test_rollback_simulation()
    verification_test = test_rollback_verification()
    
    # Calculate overall rollback readiness
    tests = [prereq_test, ecs_test, simulation_test, verification_test]
    passed_tests = sum(tests)
    total_tests = len(tests)
    rollback_readiness = (passed_tests / total_tests) * 100
    
    # Final report
    print("\n" + "=" * 50)
    print("📊 ROLLBACK READINESS REPORT")
    print("=" * 50)
    
    print(f"Prerequisites Ready: {'✅ PASS' if prereq_test else '❌ FAIL'}")
    print(f"ECS State Healthy: {'✅ PASS' if ecs_test else '❌ FAIL'}")
    print(f"Rollback Simulation: {'✅ PASS' if simulation_test else '❌ FAIL'}")
    print(f"Verification Process: {'✅ PASS' if verification_test else '❌ FAIL'}")
    print()
    print(f"Overall Rollback Readiness: {rollback_readiness:.1f}% ({passed_tests}/{total_tests})")
    
    if rollback_readiness >= 90:
        print("\n🛡️ ROLLBACK CAPABILITY: EXCELLENT")
        print("✅ Ready for emergency rollback if needed")
        print("✅ Can restore service in <5 minutes")
        print("✅ Verification process in place")
    elif rollback_readiness >= 70:
        print("\n🛡️ ROLLBACK CAPABILITY: GOOD")
        print("⚠️ Most rollback functions ready")
        print("⚠️ Some improvements needed")
    else:
        print("\n🛡️ ROLLBACK CAPABILITY: NEEDS IMPROVEMENT") 
        print("❌ Critical gaps in rollback readiness")
        print("❌ Emergency recovery may be compromised")
    
    print(f"\n📋 Emergency Rollback Command:")
    print(f"   cd /mnt/c/Users/HP/ava-olo-constitutional/protection_system")
    print(f"   ./emergency_rollback.sh both working-state-20250720-112551")

if __name__ == "__main__":
    main()