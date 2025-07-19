#!/usr/bin/env python3
"""
Test JSON Parsing Fallback for GPT-4 Responses
"""

import json
import re
import logging

logger = logging.getLogger(__name__)

def parse_gpt4_response(content):
    """
    Parse GPT-4 response with multiple fallback strategies
    This mirrors the logic in cava_registration_llm.py
    """
    # Parse response with enhanced fallback
    try:
        result = json.loads(content)
        return result, "Direct JSON parse"
    except json.JSONDecodeError:
        # Try to extract JSON from response
        
        # Try different JSON patterns
        json_patterns = [
            r'\{.*\}',  # Standard JSON
            r'```json\s*(\{.*?\})\s*```',  # Markdown code block
            r'```\s*(\{.*?\})\s*```',  # Code block without json tag
        ]
        
        for pattern in json_patterns:
            json_match = re.search(pattern, content, re.DOTALL)
            if json_match:
                try:
                    json_str = json_match.group(1) if '```' in pattern else json_match.group()
                    result = json.loads(json_str)
                    return result, f"Extracted with pattern: {pattern}"
                except:
                    continue
        
        # Create fallback structure
        logger.warning(f"GPT-4 returned non-JSON, using fallback: {content[:100]}...")
        
        # Check if it looks like a clarification question
        if "?" in content or "mean" in content.lower():
            return {
                "response": content,
                "extracted_data": {},
                "language_detected": "en"
            }, "Fallback - Question"
        
        # Pure text response - create structure
        return {
            "response": content if content else "I'm here to help you register. What's your name?",
            "extracted_data": {},
            "language_detected": "en"
        }, "Fallback - Text"

def test_json_parsing():
    """Test various JSON response formats"""
    
    test_cases = [
        # Valid JSON
        ('{"response": "Hello!", "extracted_data": {"first_name": "Peter"}}', "Valid JSON"),
        
        # JSON with whitespace
        ('\n\n{"response": "Hello!", "extracted_data": {}}\n\n', "JSON with whitespace"),
        
        # Markdown code block
        ('```json\n{"response": "Hello!", "extracted_data": {}}\n```', "Markdown JSON block"),
        
        # Code block without json tag
        ('```\n{"response": "Hello!", "extracted_data": {}}\n```', "Plain code block"),
        
        # JSON with prefix text
        ('Sure! Here is the JSON:\n{"response": "Hello!", "extracted_data": {}}', "JSON with prefix"),
        
        # Plain text response
        ('Hello! What is your name?', "Plain text"),
        
        # Question response
        ('How do you mean that?', "Question"),
        
        # Empty response
        ('', "Empty response"),
        
        # Complex nested JSON
        ('{"response": "Hi!", "extracted_data": {"first_name": null, "last_name": null, "farm_location": "Ljubljana", "primary_crops": null, "whatsapp_number": null}}', "Complex JSON"),
        
        # Malformed JSON
        ('{"response": "Hello", "extracted_data": {', "Malformed JSON"),
    ]
    
    print("🧪 TESTING JSON PARSING FALLBACK")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for i, (test_input, description) in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {description}")
        print(f"Input: {test_input[:50]}..." if len(test_input) > 50 else f"Input: {test_input}")
        
        try:
            result, method = parse_gpt4_response(test_input)
            
            # Validate result structure
            if isinstance(result, dict) and "response" in result and "extracted_data" in result:
                print(f"✅ PASS - Method: {method}")
                print(f"   Response: {result['response'][:50]}...")
                print(f"   Extracted: {result.get('extracted_data', {})}")
                passed += 1
            else:
                print(f"❌ FAIL - Invalid result structure")
                failed += 1
                
        except Exception as e:
            print(f"❌ FAIL - Exception: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"🏁 RESULTS: {passed} passed, {failed} failed")
    print("✅ All tests passed!" if failed == 0 else "❌ Some tests failed")

if __name__ == "__main__":
    test_json_parsing()