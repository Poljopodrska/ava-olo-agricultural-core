#!/usr/bin/env python3
"""
CAVA Memory System Test Script
Tests the complete CAVA implementation including:
- Message storage and retrieval
- Fact extraction and storage  
- Context building and memory
- Cost tracking with GPT-3.5
"""
import asyncio
import json
import logging
from datetime import datetime
from modules.api.chat_routes import router as chat_router
from modules.cava.conversation_memory import CAVAMemory
from modules.cava.fact_extractor import FactExtractor
from modules.core.database_manager import DatabaseManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_cava_memory_system():
    """Test the complete CAVA memory system with a Bulgarian mango farmer scenario"""
    
    print("🧪 Testing CAVA Memory System")
    print("=" * 50)
    
    # Test phone number - Bulgarian mango farmer
    test_phone = "+359887654321"
    
    # Initialize CAVA components
    cava_memory = CAVAMemory()
    fact_extractor = FactExtractor()
    db_manager = DatabaseManager()
    
    print(f"📱 Testing with phone number: {test_phone}")
    
    # Test conversation messages that should trigger memory and fact extraction
    test_messages = [
        {
            "message": "Здравей! Аз съм Димитър и отглеждам манго в Пловдив. Имам проблем с вредители по листата.",
            "expected_facts": ["crops", "location", "problem_type"]
        },
        {
            "message": "Използвам азотен тор всяка седмица, но растенията не растат добре. Трябва ли да сменя торене?",
            "expected_facts": ["fertilizer_type", "frequency", "growth_issues"]
        },
        {
            "message": "Миналия месец пръскам с инсектицид Decis, но все още има щети. Кога да повторя пръскането?",
            "expected_facts": ["pesticide_used", "application_timing", "effectiveness"]
        },
        {
            "message": "Полето ми е 2.5 хектара и очаквам около 15 тона реколта. Нормално ли е това?",
            "expected_facts": ["field_size", "expected_yield", "yield_assessment"]
        },
        {
            "message": "Благодаря за съветите! Ще тествам органичните торове които препоръча.",
            "expected_facts": ["feedback", "organic_fertilizers", "willingness_to_try"]
        }
    ]
    
    # Test 1: Message Storage and Context Building
    print("\n1️⃣ Testing Message Storage and Context Building")
    print("-" * 40)
    
    conversation_history = []
    
    for i, test_case in enumerate(test_messages, 1):
        message = test_case["message"]
        print(f"\nMessage {i}: {message[:50]}...")
        
        try:
            # Store the user message
            await store_message_test(test_phone, 'user', message)
            
            # Get conversation context
            context = await cava_memory.get_enhanced_context(test_phone)
            
            print(f"   📝 Context summary: {context['context_summary']}")
            print(f"   💬 Messages in context: {len(context['messages'])}")
            
            # Test fact extraction
            facts = await fact_extractor.extract_facts(message, context['context_summary'])
            
            if facts:
                print(f"   🧠 Extracted facts: {json.dumps(facts, indent=6, ensure_ascii=False)}")
                
                # Store the facts
                await cava_memory.store_extracted_facts(test_phone, facts)
                
                # Verify fact storage
                stored_facts = await cava_memory.get_farmer_facts(test_phone)
                print(f"   💾 Total stored facts: {len(stored_facts)}")
            else:
                print("   ❌ No facts extracted")
            
            # Simulate assistant response for memory continuity
            assistant_response = f"Разбирам проблема ви, Димитър. Ще ви помогна с {test_case['expected_facts'][0] if test_case['expected_facts'] else 'вашия въпрос'}."
            await store_message_test(test_phone, 'assistant', assistant_response)
            
            conversation_history.append({
                'user_message': message,
                'assistant_response': assistant_response,
                'facts_extracted': facts,
                'context_length': len(context['messages'])
            })
            
        except Exception as e:
            print(f"   ❌ Error in message {i}: {str(e)}")
    
    # Test 2: Memory Persistence and Retrieval
    print("\n2️⃣ Testing Memory Persistence and Retrieval")
    print("-" * 40)
    
    try:
        # Get full conversation history
        final_context = await cava_memory.get_enhanced_context(test_phone, limit=20)
        
        print(f"📊 Final Statistics:")
        print(f"   - Total messages: {len(final_context['messages'])}")
        print(f"   - Farmer info: {final_context['farmer'] is not None}")
        print(f"   - Stored facts: {len(final_context.get('stored_facts', []))}")
        print(f"   - Context summary: {final_context['context_summary']}")
        
        # Display stored facts by type
        if final_context.get('stored_facts'):
            print(f"\n📋 Stored Facts by Type:")
            fact_types = {}
            for fact in final_context['stored_facts']:
                fact_type = fact['fact_type']
                if fact_type not in fact_types:
                    fact_types[fact_type] = []
                fact_types[fact_type].append(fact['fact_data'])
            
            for fact_type, facts in fact_types.items():
                print(f"   - {fact_type}: {len(facts)} entries")
                
    except Exception as e:
        print(f"❌ Error testing memory persistence: {str(e)}")
    
    # Test 3: Memory-based Response Generation
    print("\n3️⃣ Testing Memory-based Response Generation")
    print("-" * 40)
    
    try:
        # Test with a follow-up question that requires memory
        follow_up = "Какво беше името на пестицида който споменах?"
        
        print(f"Follow-up question: {follow_up}")
        
        # Get context for this follow-up
        context = await cava_memory.get_enhanced_context(test_phone)
        
        # Check if context contains previous pesticide information
        context_text = context['context_summary'].lower()
        messages_text = ' '.join([msg['content'].lower() for msg in context['messages']])
        
        has_pesticide_memory = 'decis' in context_text or 'decis' in messages_text
        
        print(f"   🧠 Memory of pesticide 'Decis': {'✅ Found' if has_pesticide_memory else '❌ Missing'}")
        print(f"   📝 Context includes: {len(context['messages'])} messages, {len(context.get('stored_facts', []))} facts")
        
        # Simulate what GPT would see
        if context['stored_facts']:
            pesticide_facts = [f for f in context['stored_facts'] if 'pesticide' in f.get('fact_type', '').lower()]
            if pesticide_facts:
                print(f"   💊 Pesticide facts available: {len(pesticide_facts)}")
                for fact in pesticide_facts[:2]:  # Show first 2
                    print(f"      - {fact['fact_type']}: {fact['fact_data']}")
                    
    except Exception as e:
        print(f"❌ Error testing memory-based responses: {str(e)}")
    
    # Test 4: Database Integration Test
    print("\n4️⃣ Testing Database Integration")
    print("-" * 40)
    
    try:
        # Test table existence and data
        async with db_manager.get_connection_async() as conn:
            # Check chat_messages table
            messages_count = await conn.fetchval(
                "SELECT COUNT(*) FROM chat_messages WHERE wa_phone_number = $1", 
                test_phone
            )
            
            # Check farmer_facts table  
            facts_count = await conn.fetchval(
                "SELECT COUNT(*) FROM farmer_facts WHERE farmer_phone = $1",
                test_phone
            )
            
            print(f"📊 Database Statistics:")
            print(f"   - Messages stored: {messages_count}")
            print(f"   - Facts stored: {facts_count}")
            
            # Show recent messages
            if messages_count > 0:
                recent_messages = await conn.fetch(
                    "SELECT role, content, timestamp FROM chat_messages WHERE wa_phone_number = $1 ORDER BY timestamp DESC LIMIT 3",
                    test_phone
                )
                
                print(f"\n📝 Recent Messages:")
                for msg in recent_messages:
                    print(f"   {msg['role']}: {msg['content'][:60]}... ({msg['timestamp']})")
                    
    except Exception as e:
        print(f"❌ Database integration error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 CAVA Memory System Test Complete!")
    print("\nNote: This test simulates the full CAVA conversation flow:")
    print("- ✅ Message storage in PostgreSQL")
    print("- ✅ Context retrieval with farmer info")
    print("- ✅ Fact extraction and structured storage")
    print("- ✅ Memory persistence across conversations")
    print("- ✅ Enhanced context with stored facts")

async def store_message_test(wa_phone_number: str, role: str, content: str):
    """Test helper to store messages directly"""
    try:
        db_manager = DatabaseManager()
        query = """
            INSERT INTO chat_messages (wa_phone_number, role, content, timestamp)
            VALUES ($1, $2, $3, NOW())
        """
        
        async with db_manager.get_connection_async() as conn:
            await conn.execute(query, wa_phone_number, role, content)
            
    except Exception as e:
        print(f"Failed to store test message: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_cava_memory_system())