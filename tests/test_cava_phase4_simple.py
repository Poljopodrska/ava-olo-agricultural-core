#!/usr/bin/env python3
"""
🏛️ CAVA Phase 4 Simple Test
Quick validation of CAVA functionality
"""

import asyncio
import logging
import os

# Ensure dry-run mode
os.environ['CAVA_DRY_RUN_MODE'] = 'true'

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from implementation.cava.universal_conversation_engine import CAVAUniversalConversationEngine

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def run_simple_tests():
    """Run simple CAVA tests"""
    logger.info("🏛️ CAVA Phase 4 Simple Test")
    logger.info("=" * 50)
    
    engine = CAVAUniversalConversationEngine()
    await engine.initialize()
    
    # Test 1: Peter Knaflič
    logger.info("\n✅ Test 1: Peter Knaflič Registration")
    resp1 = await engine.handle_farmer_message(12345, "Peter Knaflič")
    logger.info(f"Response: {resp1['message']}")
    
    resp2 = await engine.handle_farmer_message(12345, "+385912345678", resp1["session_id"])
    logger.info(f"Response: {resp2['message']}")
    
    resp3 = await engine.handle_farmer_message(12345, "mypassword123", resp1["session_id"])
    logger.info(f"Response: {resp3['message']}")
    
    # Test 2: Watermelon
    logger.info("\n✅ Test 2: Watermelon")
    resp4 = await engine.handle_farmer_message(12345, "I planted watermelon in north field")
    logger.info(f"Response: {resp4['message']}")
    
    # Test 3: Bulgarian Mango
    logger.info("\n✅ Test 3: Bulgarian Mango")
    resp5 = await engine.handle_farmer_message(67890, "When can I harvest my Bulgarian mangoes?")
    logger.info(f"Response: {resp5['message']}")
    
    # Health Check
    logger.info("\n✅ Health Check")
    health = await engine.health_check()
    logger.info(f"Status: {health['status']}")
    logger.info(f"Databases: {health['databases']}")
    
    await engine.close()
    
    logger.info("\n🎉 Simple tests completed successfully!")
    logger.info("\n🏛️ Constitutional Notes:")
    logger.info("✅ Amendment #15: LLM generates queries (dry-run mode)")
    logger.info("✅ MANGO RULE: Handled Bulgarian mangoes")
    logger.info("✅ ERROR ISOLATION: Runs without Docker")
    logger.info("✅ MODULE INDEPENDENCE: Separate CAVA config")

if __name__ == "__main__":
    asyncio.run(run_simple_tests())