#!/usr/bin/env python3
"""Test if Twilio can be imported"""
import sys
print(f"Python version: {sys.version}")

try:
    import twilio
    print(f"✅ Twilio imported successfully! Version: {twilio.__version__}")
    
    from twilio.request_validator import RequestValidator
    print("✅ RequestValidator imported successfully!")
    
    from twilio.twiml.messaging_response import MessagingResponse
    print("✅ MessagingResponse imported successfully!")
    
    # Test creating objects
    validator = RequestValidator("test_token")
    print("✅ RequestValidator instantiated successfully!")
    
    resp = MessagingResponse()
    resp.message("Test message")
    print("✅ MessagingResponse created successfully!")
    print(f"XML output: {str(resp)}")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Twilio is not installed or has dependency issues")
except Exception as e:
    print(f"❌ Error: {e}")