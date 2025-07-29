#!/usr/bin/env python3
"""
Test WhatsApp webhook directly with detailed response analysis
"""
import requests
import time
import re

BASE_URL = "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"

print("=== Direct WhatsApp Webhook Test ===\n")

# Test data
test_data = {
    "From": "whatsapp:+1234567890",
    "To": "whatsapp:+385919857451",
    "Body": "Hello AVA, I need help with my mango farm irrigation system",
    "MessageSid": "SM1234567890abcdef",
    "AccountSid": "ACtest",
    "NumMedia": "0"
}

# Wait a bit for deployment
print("Waiting 30 seconds for deployment to complete...")
time.sleep(30)

# Test the webhook
print("\nTesting main webhook...")
response = requests.post(f"{BASE_URL}/api/v1/whatsapp/webhook", data=test_data)

print(f"Status Code: {response.status_code}")
print(f"Headers: {dict(response.headers)}")
print(f"\nRaw Response:\n{response.text}")

# Parse the response
if response.status_code == 200:
    # Extract message from TwiML
    match = re.search(r'<Message>(.*?)</Message>', response.text, re.DOTALL)
    if match:
        message = match.group(1)
        print(f"\nExtracted Message:\n{message}")
        
        # Check for error patterns
        if "I'm sorry, I encountered an error" in message:
            print("\n❌ STILL GETTING GENERIC ERROR!")
        elif "Debug:" in message:
            print("\n⚠️  Getting debug message - specific error identified")
        else:
            print("\n✅ SUCCESS! Got intelligent response from CAVA!")

# Test the minimal webhook
print("\n\nTesting minimal webhook...")
response = requests.post(f"{BASE_URL}/api/v1/whatsapp/webhook-minimal", data=test_data)
print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    match = re.search(r'<Message>(.*?)</Message>', response.text, re.DOTALL)
    if match:
        print(f"Minimal webhook message: {match.group(1)[:100]}...")

# Check version
print("\n\nChecking deployed version...")
response = requests.get(f"{BASE_URL}/")
match = re.search(r'content="(v[\d.]+)"', response.text)
if match:
    print(f"Deployed version: {match.group(1)}")