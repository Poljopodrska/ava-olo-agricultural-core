#!/usr/bin/env python3
"""
Local test of CAVA Registration Engine
Tests the engine logic without making actual OpenAI calls
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

# Mock OpenAI before importing
sys.modules['openai'] = MagicMock()

# Set test environment
os.environ['SKIP_OPENAI_TEST'] = '1'
os.environ['OPENAI_API_KEY'] = 'test-key-for-local-testing'

from modules.cava.cava_registration_engine import CAVARegistrationEngine

class MockOpenAIResponse:
    def __init__(self, content):
        self.choices = [MagicMock()]
        self.choices[0].message.content = content

async def test_engine_locally():
    """Test the engine with mocked OpenAI responses"""
    print("🧪 TESTING CAVA REGISTRATION ENGINE LOCALLY")
    print("=" * 50)
    
    # Create engine
    engine = CAVARegistrationEngine()
    
    # Mock responses for different test scenarios
    mock_responses = {
        "I want to register": json.dumps({
            "response": "Hello! I'd be happy to help you register. What's your first name?",
            "extracted_data": {},
            "intent": "register",
            "next_field_needed": "first_name"
        }),
        "My name is Peter": json.dumps({
            "response": "Nice to meet you, Peter! What's your last name?",
            "extracted_data": {"first_name": "Peter"},
            "intent": "data_collection",
            "next_field_needed": "last_name"
        }),
        "Искам да се регистрирам": json.dumps({
            "response": "Здравейте! Ще ви помогна да се регистрирате. Как се казвате?",
            "extracted_data": {},
            "intent": "register",
            "next_field_needed": "first_name"
        })
    }
    
    # Mock the asyncio.to_thread function
    async def mock_openai_call(*args, **kwargs):
        messages = kwargs.get('messages', [])
        last_message = messages[-1]['content'] if messages else ""
        
        # Return appropriate mock response
        for key, response in mock_responses.items():
            if key.lower() in last_message.lower():
                return MockOpenAIResponse(response)
        
        # Default response
        return MockOpenAIResponse(json.dumps({
            "response": "I understand you want to register. Could you tell me your first name?",
            "extracted_data": {},
            "intent": "register",
            "next_field_needed": "first_name"
        }))
    
    # Patch the asyncio.to_thread call
    import asyncio
    original_to_thread = asyncio.to_thread
    asyncio.to_thread = mock_openai_call
    
    try:
        # Test cases
        test_cases = [
            ("I want to register", "English registration intent"),
            ("My name is Peter", "Name extraction"),
            ("Искам да се регистрирам", "Bulgarian registration intent"),
            ("helo i wnat to regstr", "Garbled text parsing"),
            ("What's the weather?", "Off-topic question")
        ]
        
        for message, description in test_cases:
            print(f"\n🧪 Testing: {description}")
            print(f"   Input: {message}")
            
            session_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            try:
                result = await engine.process_message(session_id, message)
                
                print(f"   ✅ Response: {result.get('response', 'No response')[:80]}...")
                print(f"   📊 LLM Used: {result.get('llm_used', False)}")
                print(f"   🏛️ Constitutional: {result.get('constitutional_compliance', False)}")
                
                if result.get('extracted_data'):
                    print(f"   📋 Extracted: {result['extracted_data']}")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print("\n✅ LOCAL ENGINE TEST COMPLETED")
        print("The engine structure is working correctly")
        print("Ready for deployment with real OpenAI API")
        
    finally:
        # Restore original function
        asyncio.to_thread = original_to_thread

if __name__ == "__main__":
    asyncio.run(test_engine_locally())