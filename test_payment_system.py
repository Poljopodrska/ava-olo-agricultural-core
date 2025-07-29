#!/usr/bin/env python3
"""
Test Stripe Payment System
Tests the payment integration flow
"""
import asyncio
import requests
import json
import os
from datetime import datetime, timedelta

BASE_URL = "http://ava-olo-farmers-alb-82735690.us-east-1.elb.amazonaws.com"

async def test_payment_system():
    print("=== AVA OLO Payment System Test ===\n")
    
    # Test 1: Check pricing configuration
    print("1. Testing pricing configuration endpoint...")
    response = requests.get(f"{BASE_URL}/api/v1/payment/pricing")
    if response.status_code == 200:
        pricing = response.json()
        print(f"✅ Current pricing: €{pricing['monthly_price_eur']}/month")
        print(f"   API limit: {pricing['limits']['api_calls']}")
        print(f"   WhatsApp limit: {pricing['limits']['whatsapp_messages']}")
    else:
        print(f"❌ Error: {response.status_code}")
    
    # Test 2: Check subscription status for test farmer
    print("\n2. Testing subscription status endpoint...")
    farmer_id = 1  # Test with farmer ID 1
    response = requests.get(f"{BASE_URL}/api/v1/payment/status/{farmer_id}")
    if response.status_code == 200:
        status = response.json()
        print(f"✅ Farmer {farmer_id} subscription status: {status['subscription_status']}")
        print(f"   Active: {status['has_active_subscription']}")
        print(f"   API usage: {status['usage']['api_calls']['used']}/{status['usage']['api_calls']['limit']}")
    else:
        print(f"❌ Error: {response.status_code}")
    
    # Test 3: Test checkout session creation (don't actually redirect)
    print("\n3. Testing checkout session creation...")
    response = requests.post(
        f"{BASE_URL}/api/v1/payment/subscribe",
        json={
            "farmer_id": farmer_id,
            "return_url": f"{BASE_URL}/subscription-success"
        }
    )
    if response.status_code == 200:
        result = response.json()
        if result.get('status') == 'already_subscribed':
            print(f"ℹ️  Farmer already subscribed")
        else:
            print(f"✅ Checkout URL created: {result.get('checkout_url', 'N/A')[:50]}...")
    else:
        print(f"❌ Error: {response.status_code}")
    
    # Test 4: Test WhatsApp payment link generation
    print("\n4. Testing WhatsApp payment link...")
    response = requests.post(
        f"{BASE_URL}/api/v1/payment/whatsapp-payment-link",
        json={"phone": "+1234567890"}
    )
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Payment message generated successfully")
        print(f"   Message preview: {result['message'][:100]}...")
    elif response.status_code == 404:
        print(f"ℹ️  No farmer found with test phone number")
    else:
        print(f"❌ Error: {response.status_code}")
    
    # Test 5: Test usage tracking (simulate API call)
    print("\n5. Testing usage tracking...")
    # This would be tracked automatically by middleware
    print("ℹ️  Usage tracking happens automatically via middleware")
    
    # Test 6: Test admin configuration (requires auth)
    print("\n6. Testing admin configuration...")
    headers = {'X-Admin-Token': 'admin-secret-token'}
    response = requests.get(f"{BASE_URL}/api/v1/admin/pricing-config", headers=headers)
    if response.status_code == 200:
        config = response.json()
        print(f"✅ Admin config accessible")
        print(f"   Monthly price: €{config['monthly_price']}")
        print(f"   Trial days: {config['trial_days']}")
    else:
        print(f"❌ Admin access denied or error: {response.status_code}")
    
    print("\n=== Payment System Test Complete ===")


if __name__ == "__main__":
    asyncio.run(test_payment_system())