#!/usr/bin/env python3
"""
Debug test for FAVA database intent recognition
Testing exact scenario: "I want to enter my first vineyard, called Belouca, 3,2 ha"
"""
import json
import re

def simulate_current_fava_response(message: str, farmer_id: int = 123):
    """Simulate what current FAVA might be returning"""
    
    print("="*60)
    print("DEBUGGING FAVA RESPONSE")
    print("="*60)
    print(f"Farmer message: {message}")
    print("-"*60)
    
    # Current prompt might not recognize "I want to enter" as strong database intent
    # Let's check what patterns it might match
    
    # Check for database intent patterns
    database_intent_patterns = [
        r"add.*field",
        r"create.*field",
        r"new field",
        r"planted",
        r"I have.*hectares"
    ]
    
    has_weak_intent = any(re.search(p, message, re.IGNORECASE) for p in database_intent_patterns)
    
    # Check for STRONG intent (what we need to add)
    strong_intent_patterns = [
        r"I want to enter",
        r"I want to add",
        r"Please save",
        r"Add to my farm",
        r"Register my field"
    ]
    
    has_strong_intent = any(re.search(p, message, re.IGNORECASE) for p in strong_intent_patterns)
    
    print(f"Has weak intent patterns: {has_weak_intent}")
    print(f"Has STRONG intent patterns: {has_strong_intent}")
    
    # Parse the message for field data
    field_match = re.search(r'called\s+(\w+),?\s+([\d,]+)\s*ha', message, re.IGNORECASE)
    if field_match:
        field_name = field_match.group(1)
        area_str = field_match.group(2).replace(',', '.')
        area_ha = float(area_str)
        print(f"Extracted: field_name='{field_name}', area_ha={area_ha}")
    else:
        print("Could not extract field data")
        field_name = None
        area_ha = None
    
    # Simulate current (broken) response
    if not has_strong_intent or True:  # Currently doesn't recognize strong intent
        current_response = {
            "response": "What kind of grapes are you planning to grow at Belouca? This will help me give you specific advice for your vineyard.",
            "database_action": None,  # THIS IS THE PROBLEM!
            "sql_query": None,
            "needs_confirmation": False,
            "context_used": ["vineyard mentioned", "Belouca name"]
        }
        print("\nCURRENT (BROKEN) RESPONSE:")
    else:
        current_response = None
    
    print(json.dumps(current_response, indent=2))
    
    # What the response SHOULD be
    correct_response = {
        "response": "Perfect! I've saved Belouca vineyard (3.2 ha) to your farm records. What grape varieties are you planning to grow there?",
        "database_action": "INSERT",
        "sql_query": f"INSERT INTO fields (farmer_id, field_name, area_ha) VALUES ({farmer_id}, 'Belouca', 3.2)",
        "needs_confirmation": False,
        "context_used": ["I want to enter", "first vineyard", "Belouca", "3.2 ha"]
    }
    
    print("\nCORRECT RESPONSE SHOULD BE:")
    print(json.dumps(correct_response, indent=2))
    
    return current_response, correct_response

def test_intent_recognition():
    """Test various phrases for database intent"""
    test_phrases = [
        "I want to enter my first vineyard, called Belouca, 3,2 ha",
        "Add my South field, 2 hectares",
        "Please save North Orchard, 4.5 ha",
        "I have a new field called West Block",
        "My greenhouse is 500 square meters",
        "What should I plant in my field?",
        "I want to add East Vineyard to my farm, it's 2.8 hectares",
        "Register my field Sunset Hills, 5 ha"
    ]
    
    print("\n" + "="*60)
    print("TESTING DATABASE INTENT PATTERNS")
    print("="*60)
    
    for phrase in test_phrases:
        print(f"\nPhrase: '{phrase}'")
        
        # Check for STRONG database intent
        strong_patterns = [
            r"I want to enter",
            r"I want to add",
            r"Please save",
            r"Add to my farm",
            r"Register my field",
            r"^Add my",
            r"^Register"
        ]
        
        has_strong_intent = any(re.search(p, phrase, re.IGNORECASE) for p in strong_patterns)
        
        # Extract field data
        patterns = [
            r'called\s+(\w+),?\s+([\d,]+)\s*ha',
            r'field\s+(\w+),?\s+([\d,]+)\s*ha',
            r'(\w+)\s+to my farm,?\s+.*?([\d,]+)\s*hectares',
            r'(\w+),?\s+([\d,]+)\s*ha',
            r'^Add my\s+(\w+)\s+field,?\s+([\d,]+)\s*hectares'
        ]
        
        field_data = None
        for pattern in patterns:
            match = re.search(pattern, phrase, re.IGNORECASE)
            if match:
                field_name = match.group(1)
                area_str = match.group(2).replace(',', '.')
                field_data = (field_name, float(area_str))
                break
        
        print(f"  Strong Intent: {has_strong_intent}")
        print(f"  Field Data: {field_data}")
        print(f"  Action: {'INSERT' if has_strong_intent and field_data else 'None'}")

def main():
    print("FAVA Database Intent Debug Test")
    print("Testing exact scenario from screenshot")
    print()
    
    # Test the exact message from the screenshot
    exact_message = "I want to enter my first vineyard, called Belouca, 3,2 ha"
    current, correct = simulate_current_fava_response(exact_message)
    
    # Test intent patterns
    test_intent_recognition()
    
    print("\n" + "="*60)
    print("DIAGNOSIS:")
    print("="*60)
    print("PROBLEM: FAVA prompt doesn't recognize 'I want to enter' as database intent")
    print("SOLUTION: Update prompt to include strong intent patterns")
    print("FIX: Ensure SQL execution in chat_routes.py")
    print("="*60)

if __name__ == "__main__":
    main()