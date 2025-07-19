"""
OpenAI API Setup Verification
MUST pass before any intelligence testing
"""
import os
from dotenv import load_dotenv

def verify_openai_setup():
    """MUST pass before ANY other tests"""
    
    # Load environment
    load_dotenv()
    
    print("🔍 Verifying OpenAI API Setup...")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ FATAL: OPENAI_API_KEY not found in environment")
        return False
    
    print(f"✅ API Key found (length: {len(api_key)})")
    
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=api_key)
        
        # Make actual API call
        print("🔗 Testing API connection...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say exactly 'CAVA LLM ACTIVE' and nothing else"}],
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip()
        print(f"📡 LLM Response: '{result}'")
        
        if "CAVA LLM ACTIVE" not in result:
            print("❌ FAIL: LLM not responding correctly")
            return False
            
        print("✅ OpenAI API verified and working")
        print(f"✅ Model: {response.model}")
        print(f"✅ Usage: {response.usage.total_tokens} tokens")
        return True
        
    except Exception as e:
        print(f"❌ FATAL: OpenAI API not working: {e}")
        print("Cannot proceed without LLM access")
        return False

if __name__ == "__main__":
    success = verify_openai_setup()
    if not success:
        exit(1)
    print("\n🎯 Ready for intelligence testing!")