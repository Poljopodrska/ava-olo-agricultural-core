#!/usr/bin/env python3
"""
CAVA Test with TRUE Isolation - Shows only NEW extractions per message
"""

import asyncio
import json
from datetime import datetime
from cava_registration_llm import get_llm_registration_engine, registration_sessions, reset_all_sessions

async def test_true_isolation():
    """Test with complete isolation showing only NEW data extracted"""
    
    print("🧪 CAVA TRUE ISOLATION TEST")
    print("=" * 70)
    print("This test shows ONLY what's extracted from each individual message\n")
    
    # Reset everything
    reset_all_sessions()
    
    # Test case: Simple Peter flow
    test_messages = [
        ("Peter", "Should extract only first_name"),
        ("Knaflič", "Should extract only last_name"),
        ("+38640123456", "Should extract only phone"),
        ("Ljubljana", "Should extract only location"),
        ("corn", "Should extract only crops")
    ]
    
    llm = await get_llm_registration_engine()
    session_id = f"isolation_test_{int(datetime.now().timestamp())}"
    conversation_history = []
    
    previous_data = {}
    
    for i, (message, expected) in enumerate(test_messages, 1):
        print(f"\n--- Exchange {i}: {expected} ---")
        print(f"👤 FARMER: {message}")
        
        # Get response
        result = await llm.process_registration_message(
            message=message,
            session_id=session_id,
            conversation_history=conversation_history
        )
        
        print(f"🤖 AVA: {result['response'][:80]}...")
        
        # Calculate what's NEW in this exchange
        current_data = result['extracted_data']
        new_extractions = {}
        
        for field, value in current_data.items():
            if field not in previous_data or previous_data.get(field) != value:
                if value is not None:  # Only show non-null new values
                    new_extractions[field] = value
        
        print(f"🆕 NEW EXTRACTIONS: {json.dumps(new_extractions, indent=2)}")
        print(f"📊 TOTAL COLLECTED: {json.dumps(current_data, indent=2)}")
        
        # Check if extraction matches expectation
        if i == 1 and len(new_extractions) == 1 and 'first_name' in new_extractions:
            print("✅ CLEAN: Only first_name extracted from 'Peter'")
        elif i == 1 and len(new_extractions) > 1:
            print("❌ CONTAMINATED: Multiple fields extracted from just 'Peter'!")
            print(f"   Unexpected fields: {[k for k in new_extractions if k != 'first_name']}")
        
        # Update for next iteration
        previous_data = current_data.copy()
        conversation_history.append({"message": message, "is_farmer": True})
        conversation_history.append({"message": result['response'], "is_farmer": False})
    
    # Final check
    print("\n" + "="*70)
    print("ISOLATION TEST COMPLETE")
    print("="*70)
    
    if session_id in registration_sessions:
        final_data = registration_sessions[session_id]['collected_data']
        print(f"Final collected data: {json.dumps(final_data, indent=2)}")
        
        # Clean up
        del registration_sessions[session_id]

if __name__ == "__main__":
    asyncio.run(test_true_isolation())