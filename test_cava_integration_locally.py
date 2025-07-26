#!/usr/bin/env python3
"""
CAVA Integration Local Test Suite - Run BEFORE deployment!
Tests all CAVA functionality locally to avoid wasted deployment cycles.

Usage: python test_cava_integration_locally.py

This script simulates the MANGO TEST scenario and verifies all CAVA components.
Only deploy if this returns a score of 50+/60.
"""
import asyncio
import sys
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.core.database_manager import DatabaseManager
from modules.cava.conversation_memory import CAVAMemory
from modules.cava.fact_extractor import FactExtractor

class CAVALocalTester:
    def __init__(self):
        self.test_phone = f"+385999{datetime.now().strftime('%H%M%S')}"
        self.db_manager = DatabaseManager()
        self.cava_memory = CAVAMemory()
        self.fact_extractor = FactExtractor()
        
        # Test results - each component out of 10 points
        self.results = {
            "database_connection": 0,
            "message_storage": 0,
            "context_retrieval": 0,
            "fact_extraction": 0,
            "memory_persistence": 0,
            "llm_context_usage": 0
        }
        
        self.test_messages = [
            "Hello, I'm a farmer from Bulgaria",
            "I grow mangoes on my farm",
            "I have 5 hectares of mango trees",
            "When should I harvest my mangoes?",
            "What fertilizer do you recommend for my mangoes?"
        ]
    
    async def run_all_tests(self):
        """Run complete CAVA test suite"""
        print("🧪 CAVA Integration Local Test Suite")
        print("=" * 50)
        print(f"Test farmer: {self.test_phone}")
        print(f"Started: {datetime.now().isoformat()}")
        print()
        
        try:
            # Test 1: Database Connection
            await self.test_database_connection()
            
            # Test 2: Message Storage
            await self.test_message_storage()
            
            # Test 3: Context Retrieval
            await self.test_context_retrieval()
            
            # Test 4: Fact Extraction
            await self.test_fact_extraction()
            
            # Test 5: Memory Persistence (MANGO TEST)
            await self.test_memory_persistence()
            
            # Test 6: LLM Context Usage
            await self.test_llm_context_usage()
            
            # Calculate results
            return await self.calculate_final_score()
            
        except Exception as e:
            print(f"❌ Test suite crashed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_database_connection(self):
        """Test 1: Database Connection (10 points)"""
        print("1️⃣ Testing Database Connection...")
        
        try:
            # Test basic connection
            async with self.db_manager.get_connection_async() as conn:
                result = await conn.fetchval("SELECT 1")
                
                if result == 1:
                    # Check CAVA tables exist
                    tables_exist = await conn.fetchval("""
                        SELECT COUNT(*) FROM information_schema.tables 
                        WHERE table_name IN ('chat_messages', 'farmer_facts', 'llm_usage_log')
                    """)
                    
                    if tables_exist >= 3:
                        self.results["database_connection"] = 10
                        print("   ✅ Database connected, all CAVA tables exist")
                    else:
                        self.results["database_connection"] = 5
                        print(f"   ⚠️ Database connected but only {tables_exist}/3 CAVA tables exist")
                else:
                    print("   ❌ Database connection failed")
                    
        except Exception as e:
            print(f"   ❌ Database error: {str(e)}")
    
    async def test_message_storage(self):
        """Test 2: Message Storage (10 points)"""
        print("\n2️⃣ Testing Message Storage...")
        
        try:
            # Store test messages
            async with self.db_manager.get_connection_async() as conn:
                # Store user message
                await conn.execute("""
                    INSERT INTO chat_messages (wa_phone_number, role, content, timestamp)
                    VALUES ($1, $2, $3, NOW())
                """, self.test_phone, 'user', self.test_messages[0])
                
                # Store assistant message
                await conn.execute("""
                    INSERT INTO chat_messages (wa_phone_number, role, content, timestamp)
                    VALUES ($1, $2, $3, NOW())
                """, self.test_phone, 'assistant', 'Hello! How can I help you with your farming?')
                
                # Check storage
                count = await conn.fetchval("""
                    SELECT COUNT(*) FROM chat_messages 
                    WHERE wa_phone_number = $1
                """, self.test_phone)
                
                if count >= 2:
                    self.results["message_storage"] = 10
                    print(f"   ✅ Messages stored successfully ({count} messages)")
                else:
                    print(f"   ❌ Message storage failed ({count} messages)")
                    
        except Exception as e:
            print(f"   ❌ Message storage error: {str(e)}")
    
    async def test_context_retrieval(self):
        """Test 3: Context Retrieval (10 points)"""
        print("\n3️⃣ Testing Context Retrieval...")
        
        try:
            # Get conversation context
            context = await self.cava_memory.get_conversation_context(self.test_phone)
            
            if context and context.get('messages'):
                message_count = len(context['messages'])
                has_summary = bool(context.get('context_summary'))
                
                if message_count >= 2 and has_summary:
                    self.results["context_retrieval"] = 10
                    print(f"   ✅ Context retrieved: {message_count} messages, summary: '{context['context_summary'][:50]}...'")
                elif message_count >= 1:
                    self.results["context_retrieval"] = 7
                    print(f"   ⚠️ Partial context: {message_count} messages")
                else:
                    self.results["context_retrieval"] = 3
                    print("   ⚠️ Context retrieved but no messages")
            else:
                print("   ❌ No context retrieved")
                
        except Exception as e:
            print(f"   ❌ Context retrieval error: {str(e)}")
    
    async def test_fact_extraction(self):
        """Test 4: Fact Extraction (10 points)"""
        print("\n4️⃣ Testing Fact Extraction...")
        
        try:
            # Test fact extraction from agricultural message
            test_message = "I grow mangoes on 5 hectares in Bulgaria"
            context_summary = "Bulgarian farmer"
            
            facts = await self.fact_extractor.extract_facts(test_message, context_summary)
            
            if facts:
                # Store extracted facts
                await self.cava_memory.store_extracted_facts(self.test_phone, facts)
                
                # Verify facts were stored
                stored_facts = await self.cava_memory.get_farmer_facts(self.test_phone)
                
                if stored_facts:
                    self.results["fact_extraction"] = 10
                    print(f"   ✅ Facts extracted and stored: {len(stored_facts)} fact types")
                    print(f"   Facts: {facts}")
                else:
                    self.results["fact_extraction"] = 5
                    print("   ⚠️ Facts extracted but not stored properly")
            else:
                print("   ❌ No facts extracted from agricultural message")
                
        except Exception as e:
            print(f"   ❌ Fact extraction error: {str(e)}")
    
    async def test_memory_persistence(self):
        """Test 5: Memory Persistence - The MANGO TEST! (10 points)"""
        print("\n5️⃣ Testing Memory Persistence (MANGO TEST)...")
        
        try:
            # Store multiple messages to build context
            async with self.db_manager.get_connection_async() as conn:
                for i, message in enumerate(self.test_messages[1:3], 1):  # "I grow mangoes", "I have 5 hectares"
                    await conn.execute("""
                        INSERT INTO chat_messages (wa_phone_number, role, content, timestamp)
                        VALUES ($1, $2, $3, NOW() - INTERVAL '%s minutes')
                    """ % (5 - i), self.test_phone, 'user', message)
                    
                    # Add assistant responses
                    await conn.execute("""
                        INSERT INTO chat_messages (wa_phone_number, role, content, timestamp)
                        VALUES ($1, $2, $3, NOW() - INTERVAL '%s minutes')
                    """ % (5 - i), self.test_phone, 'assistant', f'Thank you for telling me about your {message.lower()}')
            
            # Now test if context includes mango information
            context = await self.cava_memory.get_enhanced_context(self.test_phone)
            
            # Check if context remembers mangoes
            context_text = str(context).lower()
            mango_mentioned = 'mango' in context_text
            hectares_mentioned = 'hectare' in context_text or '5' in context_text
            
            if mango_mentioned and hectares_mentioned:
                self.results["memory_persistence"] = 10
                print("   ✅ MANGO TEST PASSED! Context remembers mangoes and hectares")
            elif mango_mentioned:
                self.results["memory_persistence"] = 7
                print("   ⚠️ Partial memory - remembers mangoes but not all details")
            else:
                self.results["memory_persistence"] = 0
                print("   ❌ MANGO TEST FAILED! Context doesn't remember mangoes")
                
            print(f"   Context summary: {context.get('context_summary', 'None')}")
                
        except Exception as e:
            print(f"   ❌ Memory persistence error: {str(e)}")
    
    async def test_llm_context_usage(self):
        """Test 6: LLM Context Usage (10 points)"""
        print("\n6️⃣ Testing LLM Context Usage...")
        
        try:
            # Simulate what happens in chat_routes.py
            context = await self.cava_memory.get_enhanced_context(self.test_phone)
            
            # Build messages like chat endpoint should
            messages = []
            
            # System message with context
            if context.get('context_summary'):
                system_content = f"""You are AVA, an agricultural assistant.
Context about this farmer: {context['context_summary']}
Provide specific agricultural advice."""
                messages.append({"role": "system", "content": system_content})
            
            # Add conversation history
            recent_messages = await self.cava_memory.get_conversation_messages_for_llm(self.test_phone, limit=5)
            messages.extend(recent_messages)
            
            # Add test question
            messages.append({"role": "user", "content": "When should I harvest?"})
            
            # Check if context is properly included
            full_context = str(messages).lower()
            has_system_context = any(msg.get('role') == 'system' and 'context' in msg.get('content', '').lower() for msg in messages)
            has_conversation_history = len([msg for msg in messages if msg.get('role') in ['user', 'assistant']]) > 1
            mentions_mangoes = 'mango' in full_context
            
            score = 0
            if has_system_context:
                score += 4
                print("   ✅ System message includes context")
            if has_conversation_history:
                score += 3
                print("   ✅ Conversation history included")
            if mentions_mangoes:
                score += 3
                print("   ✅ Context mentions farmer's mangoes")
            
            self.results["llm_context_usage"] = score
            
            if score >= 7:
                print(f"   ✅ LLM context properly configured ({score}/10)")
            else:
                print(f"   ⚠️ LLM context issues detected ({score}/10)")
                
            # Save debug info
            await self.save_debug_info(messages)
                
        except Exception as e:
            print(f"   ❌ LLM context usage error: {str(e)}")
    
    async def save_debug_info(self, messages: List[Dict]):
        """Save debug information for troubleshooting"""
        try:
            debug_file = f"cava_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            debug_data = {
                "test_phone": self.test_phone,
                "timestamp": datetime.now().isoformat(),
                "results": self.results,
                "llm_messages": messages,
                "message_count": len(messages)
            }
            
            with open(debug_file, 'w') as f:
                json.dump(debug_data, f, indent=2)
                
            print(f"   💾 Debug info saved to {debug_file}")
            
        except Exception as e:
            print(f"   ⚠️ Could not save debug info: {str(e)}")
    
    async def calculate_final_score(self):
        """Calculate and display final test results"""
        print("\n" + "=" * 50)
        print("📊 CAVA TEST RESULTS")
        print("=" * 50)
        
        total_score = 0
        max_score = 60  # 6 tests × 10 points each
        
        for test_name, score in self.results.items():
            icon = "✅" if score >= 8 else "⚠️" if score >= 5 else "❌"
            print(f"{icon} {test_name.replace('_', ' ').title()}: {score}/10")
            total_score += score
        
        print("-" * 50)
        print(f"🎯 TOTAL SCORE: {total_score}/{max_score} ({(total_score/max_score)*100:.1f}%)")
        
        if total_score >= 50:
            print("\n🎉 CAVA READY FOR DEPLOYMENT!")
            print("✅ All critical systems working")
            print("🚀 Safe to run: git add -A && git commit -m 'feat: CAVA complete' && git push")
            return True
        else:
            print(f"\n❌ CAVA NOT READY - Score too low ({total_score}/60)")
            print("🔧 Fix the failing tests before deploying")
            print("📋 Focus on tests with scores < 8")
            
            # Provide specific guidance
            if self.results["database_connection"] < 8:
                print("   - Check database connection and ensure CAVA tables exist")
            if self.results["message_storage"] < 8:
                print("   - Fix message storage in chat_messages table")
            if self.results["context_retrieval"] < 8:
                print("   - Fix CAVAMemory.get_conversation_context()")
            if self.results["fact_extraction"] < 8:
                print("   - Fix FactExtractor or farmer_facts table")
            if self.results["memory_persistence"] < 8:
                print("   - Fix context building - MANGO TEST failing!")
            if self.results["llm_context_usage"] < 8:
                print("   - Fix chat_routes.py to include context in LLM calls")
            
            return False
    
    async def cleanup(self):
        """Clean up test data"""
        try:
            async with self.db_manager.get_connection_async() as conn:
                await conn.execute("DELETE FROM chat_messages WHERE wa_phone_number = $1", self.test_phone)
                await conn.execute("DELETE FROM farmer_facts WHERE farmer_phone = $1", self.test_phone)
                await conn.execute("DELETE FROM llm_usage_log WHERE farmer_phone = $1", self.test_phone)
            print(f"\n🧹 Cleaned up test data for {self.test_phone}")
        except Exception as e:
            print(f"\n⚠️ Could not clean up test data: {str(e)}")

async def main():
    """Main test runner"""
    print("🧪 CAVA Pre-Deployment Test Suite")
    print("This will test all CAVA functionality locally before deployment")
    print("Only deploy if score is 50+/60!\n")
    
    tester = CAVALocalTester()
    
    try:
        success = await tester.run_all_tests()
        return success
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
        return False
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Always clean up
        try:
            await tester.cleanup()
        except:
            pass

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Failed to run tests: {str(e)}")
        sys.exit(1)