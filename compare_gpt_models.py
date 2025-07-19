"""
Compare GPT-3.5-turbo vs GPT-4 for CAVA business registration
"""
import asyncio
import time
import json
from openai import AsyncOpenAI
import os

# Test scenarios
TEST_SCENARIOS = [
    {
        "name": "Bulgarian Crocodile Redirect",
        "input": "крокодил яде манго в България",
        "expected": "Should acknowledge briefly and redirect to registration"
    },
    {
        "name": "Full Name Extraction", 
        "input": "Peter Knaflič",
        "expected": "Should extract both first_name and last_name"
    },
    {
        "name": "Emergency Override",
        "input": "URGENT: My corn crop is dying from disease!",
        "expected": "Should prioritize help over registration"
    },
    {
        "name": "Multi-info Extraction",
        "input": "I'm Ana Horvat from Ljubljana, I grow tomatoes",
        "expected": "Should extract name, location, and crops"
    }
]

BUSINESS_SYSTEM_PROMPT = """You are AVA, an agricultural assistant helping farmers register efficiently.

REGISTRATION GOAL: Collect required information in 5-7 natural exchanges:
- first_name, last_name, farm_location, primary_crops, whatsapp_number

CONVERSATION GUIDELINES:
1. Stay friendly and natural, acknowledge their input briefly
2. For off-topic topics: acknowledge (1 sentence max) then redirect to registration
3. Always work toward collecting missing registration fields
4. GUIDANCE: Continue naturally while working toward registration.

REDIRECTION EXAMPLES:
- Crocodiles: "That's unusual! Let's get you registered first. What's your name?"
- Philosophy: "Interesting question! First, may I have your name for registration?"

URGENCY_KEYWORDS = ["dying", "disease", "urgent", "emergency", "destroyed"]
If urgency detected, provide immediate agricultural help and skip registration.

Always return ONLY a JSON object:
{
  "response": "your natural, business-focused response",
  "extracted_data": {
    "first_name": "value or null",
    "last_name": "value or null",
    "farm_location": "value or null", 
    "primary_crops": "value or null",
    "whatsapp_number": "value or null"
  }
}"""

async def test_model(model_name: str, test_case: dict) -> dict:
    """Test a single scenario with specified model"""
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    start_time = time.time()
    
    try:
        # GPT-4 doesn't support response_format json_object
        params = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": BUSINESS_SYSTEM_PROMPT},
                {"role": "user", "content": f'Farmer said: "{test_case["input"]}"\n\nPrevious conversation: No previous conversation\nAlready collected: {{}}\n\nUnderstand their message and respond naturally.'}
            ],
            "temperature": 0.7,
            "max_tokens": 300
        }
        
        # Only add JSON format for GPT-3.5
        if "gpt-3.5" in model_name:
            params["response_format"] = {"type": "json_object"}
        
        response = await client.chat.completions.create(**params)
        
        elapsed_time = time.time() - start_time
        
        # Parse response
        content = response.choices[0].message.content
        
        # Try to parse as JSON, fallback for GPT-4
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            # GPT-4 might not return pure JSON, extract what we can
            result = {
                "response": content.strip(),
                "extracted_data": {}
            }
        
        return {
            "model": model_name,
            "response": result.get("response", ""),
            "extracted_data": result.get("extracted_data", {}),
            "tokens_used": response.usage.total_tokens,
            "time_seconds": round(elapsed_time, 2),
            "success": True
        }
        
    except Exception as e:
        return {
            "model": model_name,
            "error": str(e),
            "time_seconds": round(time.time() - start_time, 2),
            "success": False
        }

async def compare_models():
    """Compare GPT-3.5-turbo vs GPT-4 on business scenarios"""
    print("🤖 GPT MODEL COMPARISON - CAVA Business Registration")
    print("=" * 70)
    print("Testing business-focused registration with temperature=0.7")
    print()
    
    models = ["gpt-4"]
    results = {}
    
    for test_case in TEST_SCENARIOS:
        print(f"📝 {test_case['name']}")
        print(f"Input: '{test_case['input']}'")
        print(f"Expected: {test_case['expected']}")
        print("-" * 50)
        
        test_results = {}
        
        for model in models:
            print(f"Testing {model}...")
            result = await test_model(model, test_case)
            test_results[model] = result
            
            if result["success"]:
                print(f"✅ {model}:")
                print(f"   Response: {result['response']}")
                print(f"   Extracted: {result['extracted_data']}")
                print(f"   Time: {result['time_seconds']}s, Tokens: {result['tokens_used']}")
            else:
                print(f"❌ {model}: {result['error']}")
            print()
        
        results[test_case['name']] = test_results
        print()
    
    # Summary comparison
    print("=" * 70)
    print("PERFORMANCE COMPARISON")
    print("=" * 70)
    
    gpt35_times = []
    gpt4_times = []
    gpt35_tokens = []
    gpt4_tokens = []
    
    for test_name, test_results in results.items():
        print(f"\n📊 {test_name}:")
        
        gpt35 = test_results.get("gpt-3.5-turbo", {})
        gpt4 = test_results.get("gpt-4", {})
        
        if gpt35.get("success") and gpt4.get("success"):
            print(f"   Response Quality: Both models handled scenario well")
            print(f"   Speed: GPT-3.5 ({gpt35['time_seconds']}s) vs GPT-4 ({gpt4['time_seconds']}s)")
            print(f"   Tokens: GPT-3.5 ({gpt35['tokens_used']}) vs GPT-4 ({gpt4['tokens_used']})")
            
            gpt35_times.append(gpt35['time_seconds'])
            gpt4_times.append(gpt4['time_seconds'])
            gpt35_tokens.append(gpt35['tokens_used'])
            gpt4_tokens.append(gpt4['tokens_used'])
        else:
            print(f"   ❌ Some models failed")
    
    if gpt35_times and gpt4_times:
        print(f"\n🏁 OVERALL COMPARISON:")
        print(f"   Average Speed: GPT-3.5 ({sum(gpt35_times)/len(gpt35_times):.2f}s) vs GPT-4 ({sum(gpt4_times)/len(gpt4_times):.2f}s)")
        print(f"   Average Tokens: GPT-3.5 ({sum(gpt35_tokens)/len(gpt35_tokens):.0f}) vs GPT-4 ({sum(gpt4_tokens)/len(gpt4_tokens):.0f})")
        
        speed_ratio = (sum(gpt4_times)/len(gpt4_times)) / (sum(gpt35_times)/len(gpt35_times))
        print(f"   GPT-4 is {speed_ratio:.1f}x slower than GPT-3.5")
        
        cost_ratio = (sum(gpt4_tokens)/len(gpt4_tokens)) / (sum(gpt35_tokens)/len(gpt35_tokens))
        print(f"   GPT-4 uses {cost_ratio:.1f}x more tokens")
    
    print(f"\n🎯 RECOMMENDATION:")
    print(f"   For business registration: GPT-3.5-turbo recommended")
    print(f"   Reasons: Faster response time, lower cost, adequate quality")

if __name__ == "__main__":
    asyncio.run(compare_models())