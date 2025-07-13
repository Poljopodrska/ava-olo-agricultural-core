#!/usr/bin/env python3
"""
Test OpenAI Connection Diagnostics
🎯 Purpose: Debug why OpenAI isn't connecting despite key being set
"""

import os
import asyncio

async def diagnose_openai():
    print("🔍 OpenAI Connection Diagnostics")
    print("=" * 50)
    
    # 1. Check environment variable
    api_key = os.getenv('OPENAI_API_KEY')
    print(f"\n1. Environment Variable Check:")
    print(f"   OPENAI_API_KEY present: {bool(api_key)}")
    if api_key:
        print(f"   Key length: {len(api_key)}")
        print(f"   Key starts with: {api_key[:7]}...")
        print(f"   Key format valid: {api_key.startswith('sk-')}")
    
    # 2. Check OpenAI library
    print(f"\n2. OpenAI Library Check:")
    try:
        import openai
        print(f"   ✅ OpenAI library imported successfully")
        print(f"   Version: {openai.__version__ if hasattr(openai, '__version__') else 'Unknown'}")
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return
    
    # 3. Try old API style (for openai 0.28.1)
    print(f"\n3. Testing Old API Style (openai 0.28.1):")
    try:
        openai.api_key = api_key
        # Old style API call
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'test'"}],
            max_tokens=10
        )
        print(f"   ✅ Old API style works!")
        print(f"   Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"   ❌ Old API failed: {str(e)[:100]}...")
    
    # 4. Try new API style (for openai 1.x)
    print(f"\n4. Testing New API Style (openai 1.x):")
    try:
        from openai import OpenAI, AsyncOpenAI
        
        # Sync client test
        try:
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Say 'test'"}],
                max_tokens=10
            )
            print(f"   ✅ New sync API works!")
            print(f"   Response: {response.choices[0].message.content}")
        except Exception as e:
            print(f"   ❌ New sync API failed: {str(e)[:100]}...")
        
        # Async client test
        try:
            async_client = AsyncOpenAI(api_key=api_key)
            response = await async_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Say 'test'"}],
                max_tokens=10
            )
            print(f"   ✅ New async API works!")
            print(f"   Response: {response.choices[0].message.content}")
        except Exception as e:
            print(f"   ❌ New async API failed: {str(e)[:100]}...")
            
    except ImportError:
        print(f"   ❌ New API style not available (wrong openai version)")
    
    print(f"\n5. Recommendations:")
    print(f"   - Check if requirements.txt was properly installed")
    print(f"   - Verify the OpenAI API key is valid and has credits")
    print(f"   - Check AWS App Runner logs for any errors")

if __name__ == "__main__":
    asyncio.run(diagnose_openai())