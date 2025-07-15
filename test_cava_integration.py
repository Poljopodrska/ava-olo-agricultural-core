#!/usr/bin/env python3
"""
Test CAVA Integration with existing registration system
Verifies the drop-in replacement works correctly
"""
import asyncio
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_cava_registration():
    """Test that registration works with CAVA backend"""
    
    logger.info("🧪 Testing CAVA Registration Integration")
    logger.info("=" * 50)
    
    # Set dry-run mode for testing
    os.environ['CAVA_DRY_RUN_MODE'] = 'true'
    os.environ['CAVA_SERVICE_URL'] = 'http://localhost:8001'
    
    # Import the registration system (now CAVA-powered)
    from registration_memory import get_conversation_memory
    
    # Test registration flow
    conversation_id = "test-12345"
    api_key = "test-key"  # Not used by CAVA but needed for compatibility
    
    # Get registration handler
    memory_chat = get_conversation_memory(conversation_id, api_key)
    
    logger.info("\n1️⃣ Test: Send name")
    result1 = await memory_chat.process_message("Peter Knaflič")
    logger.info(f"Response: {result1['message']}")
    logger.info(f"Extracted: {result1['extracted_data']}")
    
    # Verify it asks for phone
    assert "phone" in result1['message'].lower(), "Should ask for phone after name"
    
    logger.info("\n2️⃣ Test: Send phone")
    result2 = await memory_chat.process_message("+385912345678")
    logger.info(f"Response: {result2['message']}")
    logger.info(f"Extracted: {result2['extracted_data']}")
    
    # Verify it asks for password
    assert "password" in result2['message'].lower(), "Should ask for password after phone"
    
    logger.info("\n3️⃣ Test: Send password")
    result3 = await memory_chat.process_message("mypassword123")
    logger.info(f"Response: {result3['message']}")
    logger.info(f"Extracted: {result3['extracted_data']}")
    
    # Verify it asks for farm name
    assert "farm" in result3['message'].lower(), "Should ask for farm name after password"
    
    logger.info("\n4️⃣ Test: Send farm name")
    result4 = await memory_chat.process_message("Sunny Acres Farm")
    logger.info(f"Response: {result4['message']}")
    logger.info(f"Extracted: {result4['extracted_data']}")
    logger.info(f"Status: {result4['status']}")
    
    # Verify registration complete
    assert result4['status'] == "COMPLETE", "Registration should be complete"
    assert result4['extracted_data']['full_name'] == "Peter Knaflič"
    assert result4['extracted_data']['wa_phone_number'] == "+385912345678"
    assert result4['extracted_data']['password'] == "mypassword123"
    assert result4['extracted_data']['farm_name'] == "Sunny Acres Farm"
    
    logger.info("\n✅ All tests passed!")
    logger.info("🎉 CAVA integration working perfectly!")
    logger.info("\nThe existing registration form will now use CAVA centrally!")

async def main():
    """Main test runner"""
    try:
        # First check if CAVA is running
        from implementation.cava.cava_central_service import get_cava_service
        
        logger.info("Checking CAVA service...")
        cava = await get_cava_service()
        health = await cava.health_check()
        
        if not health:
            logger.error("❌ CAVA service not running!")
            logger.info("Please run: ./start_cava_central.sh")
            return
        
        logger.info("✅ CAVA service is healthy\n")
        
        # Run tests
        await test_cava_registration()
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())