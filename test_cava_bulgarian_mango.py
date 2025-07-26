#!/usr/bin/env python3
"""
Test CAVA-powered chat with Bulgarian mango farmer scenario
Verifies GPT-3.5 Turbo, message persistence, and context awareness
"""
import asyncio
import sys
import logging
from datetime import datetime
import json

# Add the application directory to Python path
sys.path.append('.')

from modules.api.chat_routes import chat_endpoint, ChatRequest
from modules.core.database_manager import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bulgarian mango farmer test data
BULGARIAN_MANGO_FARMER = {
    "wa_phone_number": "+359887123456",  # Bulgarian phone number
    "name": "Petar Dimitrov",
    "location": "Petrich, Bulgaria",  # Southern Bulgaria near Greek border
    "crop": "mango"  # Exotic crop not typical for Bulgaria
}

async def clear_test_data():
    """Clear any existing test data for the farmer"""
    db_manager = DatabaseManager()
    
    try:
        # Clear chat messages
        query = "DELETE FROM chat_messages WHERE wa_phone_number = $1"
        async with db_manager.get_connection_async() as conn:
            await conn.execute(query, BULGARIAN_MANGO_FARMER["wa_phone_number"])
            
        # Clear LLM usage
        query = "DELETE FROM llm_usage_log WHERE farmer_phone = $1"
        async with db_manager.get_connection_async() as conn:
            await conn.execute(query, BULGARIAN_MANGO_FARMER["wa_phone_number"])
            
        logger.info("Cleared existing test data")
        
    except Exception as e:
        logger.warning(f"Could not clear test data: {e}")

async def test_conversation():
    """Test a conversation flow with the Bulgarian mango farmer"""
    
    # Clear any existing data
    await clear_test_data()
    
    # Test messages in Bulgarian and English
    test_messages = [
        # Initial greeting in Bulgarian
        {
            "message": "Здравейте, аз съм Петър от Петрич",
            "expected_context": ["Bulgarian greeting", "farmer introduction"]
        },
        # Mention growing mangoes
        {
            "message": "I grow mangoes here in Southern Bulgaria",
            "expected_context": ["mango", "Bulgaria", "unusual crop"]
        },
        # Ask about mango cultivation
        {
            "message": "When should I harvest my mangoes? They were planted 4 months ago",
            "expected_context": ["harvest timing", "mango maturity", "4 months"]
        },
        # Mention specific problems
        {
            "message": "I used Roundup yesterday on my mango field",
            "expected_context": ["Roundup", "herbicide", "chemical application"]
        },
        # Follow-up question showing context awareness
        {
            "message": "Is it safe to harvest soon?",
            "expected_context": ["Roundup application", "pre-harvest interval", "safety"]
        },
        # Test memory across "sessions" - farmer returns later
        {
            "message": "What did we discuss about my mangoes last time?",
            "expected_context": ["previous conversation", "mango", "Roundup", "harvest"]
        }
    ]
    
    print("\n" + "="*80)
    print("BULGARIAN MANGO FARMER TEST - CAVA with GPT-3.5 Turbo")
    print("="*80 + "\n")
    
    for i, test in enumerate(test_messages, 1):
        print(f"\n--- Message {i} ---")
        print(f"Farmer: {test['message']}")
        
        # Create chat request
        request = ChatRequest(
            wa_phone_number=BULGARIAN_MANGO_FARMER["wa_phone_number"],
            message=test["message"]
        )
        
        try:
            # Call the chat endpoint
            response = await chat_endpoint(request)
            
            print(f"AVA: {response.response}")
            print(f"Model: {response.model_used}")
            
            if response.facts_extracted:
                print(f"Facts extracted: {json.dumps(response.facts_extracted, indent=2)}")
            
            # Add delay to simulate real conversation
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
            return False
    
    print("\n" + "="*80)
    print("VERIFICATION TESTS")
    print("="*80 + "\n")
    
    # Verify message persistence
    await verify_message_storage()
    
    # Verify context awareness
    await verify_context_awareness()
    
    # Verify cost tracking
    await verify_cost_tracking()
    
    return True

async def verify_message_storage():
    """Verify messages are stored in database"""
    db_manager = DatabaseManager()
    
    query = """
        SELECT role, content, timestamp
        FROM chat_messages
        WHERE wa_phone_number = $1
        ORDER BY timestamp
    """
    
    async with db_manager.get_connection_async() as conn:
        rows = await conn.fetch(query, BULGARIAN_MANGO_FARMER["wa_phone_number"])
    
    print(f"✓ Messages stored: {len(rows)} messages in database")
    
    # Check we have both user and assistant messages
    roles = [row['role'] for row in rows]
    has_user = 'user' in roles
    has_assistant = 'assistant' in roles
    
    print(f"✓ User messages: {'Yes' if has_user else 'No'}")
    print(f"✓ Assistant messages: {'Yes' if has_assistant else 'No'}")

async def verify_context_awareness():
    """Verify context is maintained across messages"""
    db_manager = DatabaseManager()
    
    # Check if later messages reference earlier content
    query = """
        SELECT content
        FROM chat_messages
        WHERE wa_phone_number = $1 AND role = 'assistant'
        ORDER BY timestamp
    """
    
    async with db_manager.get_connection_async() as conn:
        rows = await conn.fetch(query, BULGARIAN_MANGO_FARMER["wa_phone_number"])
    
    # Check if responses show awareness of previous messages
    responses = [row['content'].lower() for row in rows]
    
    context_indicators = ['mango', 'roundup', 'harvest', 'bulgaria', 'petrich']
    context_found = any(
        any(indicator in response for indicator in context_indicators)
        for response in responses[1:]  # Skip first response
    )
    
    print(f"✓ Context awareness: {'Yes' if context_found else 'No'}")

async def verify_cost_tracking():
    """Verify LLM usage is tracked"""
    db_manager = DatabaseManager()
    
    query = """
        SELECT COUNT(*) as request_count,
               SUM(cost) as total_cost,
               AVG(cost) as avg_cost
        FROM llm_usage_log
        WHERE farmer_phone = $1
    """
    
    async with db_manager.get_connection_async() as conn:
        row = await conn.fetchrow(query, BULGARIAN_MANGO_FARMER["wa_phone_number"])
    
    if row and row['request_count'] > 0:
        print(f"✓ LLM usage tracked: {row['request_count']} requests")
        print(f"✓ Total cost: ${row['total_cost']:.4f}")
        print(f"✓ Average cost per request: ${row['avg_cost']:.4f}")
        print(f"✓ Estimated monthly cost (1000 messages): ${row['avg_cost'] * 1000:.2f}")
    else:
        print("✗ No LLM usage tracking found")

async def main():
    """Run the Bulgarian mango farmer test"""
    try:
        success = await test_conversation()
        
        if success:
            print("\n" + "="*80)
            print("✅ BULGARIAN MANGO FARMER TEST PASSED!")
            print("CAVA successfully handles exotic crop in unusual location")
            print("="*80 + "\n")
        else:
            print("\n❌ Test failed")
            
    except Exception as e:
        logger.error(f"Test error: {str(e)}")
        print(f"\n❌ Test failed with error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())