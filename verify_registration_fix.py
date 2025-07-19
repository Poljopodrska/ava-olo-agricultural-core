"""
Final verification of CAVA registration fix
Tests the actual endpoint like a real user would
"""
import asyncio
import aiohttp
import json

async def test_registration_endpoint():
    """Test the registration endpoint with sequential messages"""
    
    session_id = "verify-fix-" + str(int(asyncio.get_event_loop().time()))
    conversation_history = []
    
    async with aiohttp.ClientSession() as session:
        base_url = "http://localhost:8080"  # Adjust if different
        
        messages = [
            "",  # Initial empty message
            "Peter",
            "Petrov", 
            "+359123456789",
            "Bulgaria",
            "mangoes"
        ]
        
        for i, message in enumerate(messages):
            print(f"\n{'='*50}")
            print(f"Step {i+1}: Sending '{message}'")
            
            payload = {
                "message": message,
                "session_id": session_id,
                "conversation_history": conversation_history
            }
            
            try:
                async with session.post(
                    f"{base_url}/api/v1/registration/cava",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"Response: {data.get('response', 'No response')}")
                        print(f"Collected data: {data.get('extracted_data', {})}")
                        print(f"Registration complete: {data.get('registration_complete', False)}")
                        
                        # Update conversation history
                        if message:
                            conversation_history.append({
                                "message": message,
                                "is_farmer": True
                            })
                        conversation_history.append({
                            "message": data.get('response', ''),
                            "is_farmer": False
                        })
                        
                        if data.get('registration_complete'):
                            print(f"\n✅ SUCCESS! Registration completed!")
                            print(f"Farmer ID: {data.get('farmer_id')}")
                            break
                    else:
                        print(f"❌ Error: HTTP {response.status}")
                        text = await response.text()
                        print(f"Response: {text}")
                        
            except aiohttp.ClientError as e:
                print(f"❌ Connection error: {e}")
                print("Make sure the server is running on port 8080")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                break
        
        print(f"\n{'='*50}")
        print("Test Summary:")
        print(f"- Messages sent: {i+1}")
        print(f"- Session ID: {session_id}")

if __name__ == "__main__":
    print("CAVA Registration Fix Verification")
    print("Testing registration flow without loops...")
    asyncio.run(test_registration_endpoint())