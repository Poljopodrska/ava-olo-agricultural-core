#!/usr/bin/env python3
"""
Test WhatsApp webhook locally to debug issues
"""
import requests
import json

# Test the debug webhook
print("Testing WhatsApp webhook debug endpoint...")

url = "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/whatsapp/webhook-debug"
data = {
    "From": "whatsapp:+1234567890",
    "To": "whatsapp:+385919857451",
    "Body": "Hello, can you help me with my mango farm?"
}

response = requests.post(url, data=data)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

# Test the CAVA engine directly
print("\n\nTesting CAVA engine...")
url = "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/whatsapp/test-cava"
response = requests.get(url)
print(f"Status: {response.status_code}")
print(f"CAVA Test: {json.dumps(response.json(), indent=2)}")

# Test the main webhook
print("\n\nTesting main webhook...")
url = "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com/api/v1/whatsapp/webhook"
response = requests.post(url, data=data)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")