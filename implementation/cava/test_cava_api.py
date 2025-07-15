#!/usr/bin/env python3
"""
🏛️ Test CAVA API
Tests the FastAPI endpoints for CAVA
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CAVAAPITester:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
    
    async def test_health(self):
        """Test health endpoint"""
        logger.info("🏥 Testing /health endpoint...")
        
        async with self.session.get(f"{self.base_url}/health") as response:
            data = await response.json()
            logger.info(f"Health Status: {data['status']}")
            logger.info(f"Databases: {json.dumps(data['databases'], indent=2)}")
            logger.info(f"Dry Run Mode: {data['dry_run_mode']}")
            return data
    
    async def test_conversation(self, farmer_id: int, message: str, session_id: str = None) -> Dict[str, Any]:
        """Test conversation endpoint"""
        logger.info(f"💬 Testing conversation: '{message}'")
        
        payload = {
            "farmer_id": farmer_id,
            "message": message,
            "channel": "telegram"
        }
        
        if session_id:
            payload["session_id"] = session_id
        
        async with self.session.post(
            f"{self.base_url}/conversation",
            json=payload
        ) as response:
            data = await response.json()
            logger.info(f"Response: {data['message']}")
            if data.get('analysis'):
                logger.info(f"Analysis: {json.dumps(data['analysis'], indent=2)}")
            return data
    
    async def test_scenarios(self):
        """Test predefined scenarios"""
        logger.info("🧪 Testing scenarios...")
        
        async with self.session.post(f"{self.base_url}/test/scenarios") as response:
            data = await response.json()
            
            for result in data['test_results']:
                status = "✅" if result['success'] else "❌"
                logger.info(f"{status} {result['test']}")
                if result.get('response'):
                    logger.info(f"   Response: {result['response']}")
                if result.get('error'):
                    logger.info(f"   Error: {result['error']}")
            
            return data
    
    async def test_peter_knaflic_flow(self):
        """Test the Peter Knaflič registration flow"""
        logger.info("\n🧑‍🌾 Testing Peter Knaflič Registration Flow")
        logger.info("=" * 50)
        
        farmer_id = 12345
        
        # Step 1: Send name
        response1 = await self.test_conversation(farmer_id, "Peter Knaflič")
        session_id = response1["session_id"]
        
        # Step 2: Send phone
        response2 = await self.test_conversation(
            farmer_id, 
            "+385912345678", 
            session_id
        )
        
        # Step 3: Send password
        response3 = await self.test_conversation(
            farmer_id,
            "mypassword123",
            session_id
        )
        
        # Step 4: Ask farming question
        response4 = await self.test_conversation(
            farmer_id,
            "I planted watermelon in north field",
            session_id
        )
        
        # Step 5: Query about watermelon
        response5 = await self.test_conversation(
            farmer_id,
            "Where is my watermelon?",
            session_id
        )
        
        logger.info("\n✅ Peter Knaflič flow completed!")
    
    async def test_bulgarian_mango(self):
        """Test Bulgarian mango scenario (MANGO RULE)"""
        logger.info("\n🥭 Testing Bulgarian Mango Scenario")
        logger.info("=" * 50)
        
        response = await self.test_conversation(
            farmer_id=67890,
            message="When can I harvest my Bulgarian mangoes?"
        )
        
        logger.info("✅ Bulgarian mango test completed!")
    
    async def test_constitutional_principles(self):
        """Test constitutional principles endpoint"""
        logger.info("\n🏛️ Testing Constitutional Principles")
        
        async with self.session.get(f"{self.base_url}/constitutional/principles") as response:
            data = await response.json()
            
            logger.info(f"Amendment 15: {data['amendment_15']['principle']}")
            logger.info(f"Key Principles: {json.dumps(data['key_principles'], indent=2)}")
            
            return data

async def run_all_tests():
    """Run all CAVA API tests"""
    logger.info("🏛️ CAVA API Test Suite")
    logger.info("=" * 70)
    
    async with CAVAAPITester() as tester:
        # Test 1: Health check
        await tester.test_health()
        
        # Test 2: Scenarios
        await tester.test_scenarios()
        
        # Test 3: Peter Knaflič flow
        await tester.test_peter_knaflic_flow()
        
        # Test 4: Bulgarian mango
        await tester.test_bulgarian_mango()
        
        # Test 5: Constitutional principles
        await tester.test_constitutional_principles()
    
    logger.info("\n🎉 All CAVA API tests completed!")

if __name__ == "__main__":
    asyncio.run(run_all_tests())