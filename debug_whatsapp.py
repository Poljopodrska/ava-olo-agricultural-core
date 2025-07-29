#!/usr/bin/env python3
"""
Debug WhatsApp integration to find the exact error
"""
import requests
import json
import time

BASE_URL = "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"

print("=== WhatsApp Integration Debug ===\n")

# Step 1: Check debug imports
print("1. Checking import paths and module structure...")
url = f"{BASE_URL}/api/v1/whatsapp/debug-imports"
response = requests.get(url)
if response.status_code == 200:
    data = response.json()
    print(f"   Current directory: {data.get('current_dir')}")
    print(f"   Modules contents: {data.get('modules_contents', [])}")
    print(f"   CAVA contents: {data.get('cava_contents', [])}")
    print(f"   Import results: {json.dumps(data.get('import_results', {}), indent=2)}")
else:
    print(f"   ERROR: Status {response.status_code}")

# Step 2: Test CAVA engine
print("\n2. Testing CAVA engine directly...")
url = f"{BASE_URL}/api/v1/whatsapp/test-cava"
response = requests.get(url)
if response.status_code == 200:
    data = response.json()
    for check, result in data.get('checks', {}).items():
        print(f"   {check}: {result}")
    if data.get('cava_response'):
        print(f"   CAVA response success: {data['cava_response'].get('success')}")
else:
    print(f"   ERROR: Status {response.status_code}")

# Step 3: Test simple webhook (no CAVA)
print("\n3. Testing simple webhook without CAVA...")
url = f"{BASE_URL}/api/v1/whatsapp/webhook-debug"
data = {
    "From": "whatsapp:+1234567890",
    "To": "whatsapp:+385919857451",
    "Body": "Test message"
}
response = requests.post(url, data=data)
print(f"   Status: {response.status_code}")
print(f"   Response: {response.text[:100]}...")

# Step 4: Test main webhook with detailed monitoring
print("\n4. Testing main webhook (this is where the error occurs)...")
print("   Sending test message and waiting for logs...")

# First, let's check the health endpoint
url = f"{BASE_URL}/api/v1/whatsapp/health"
response = requests.get(url)
if response.status_code == 200:
    health = response.json()
    print(f"   Health check: {health.get('status')}")
    for check, status in health.get('checks', {}).items():
        print(f"   - {check}: {status}")

# Now test the main webhook
url = f"{BASE_URL}/api/v1/whatsapp/webhook"
data = {
    "From": "whatsapp:+1234567890",
    "To": "whatsapp:+385919857451",
    "Body": "Hello, I need help with my mango farm irrigation"
}
response = requests.post(url, data=data)
print(f"\n   Main webhook status: {response.status_code}")
print(f"   Main webhook response: {response.text}")

# Step 5: Try to get more specific error info
print("\n5. Checking for specific error patterns...")
if "Debug:" in response.text:
    # Extract debug message
    import re
    debug_match = re.search(r'Debug: ([^<]+)', response.text)
    if debug_match:
        print(f"   DEBUG MESSAGE: {debug_match.group(1)}")

print("\n=== Debug Complete ===")