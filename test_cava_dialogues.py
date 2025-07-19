#!/usr/bin/env python3
"""
CAVA Registration Test Protocol with Full Dialogue Output
Shows complete conversations, not just pass/fail
"""

import asyncio
import json
from datetime import datetime
from cava_registration_llm import get_llm_registration_engine, registration_sessions

# Test cases with expected outcomes
DIALOGUE_TEST_CASES = [
    {
        "name": "Simple Peter Test",
        "messages": ["Peter", "Knaflič", "+38640123456", "Ljubljana", "corn"],
        "description": "Basic registration flow with single-word answers"
    },
    {
        "name": "Ljubljana First Test", 
        "messages": ["Ljubljana"],
        "description": "What happens when they start with a city name?"
    },
    {
        "name": "Full Name Test",
        "messages": ["Peter Knaflič"],
        "description": "Should extract both first and last name"
    },
    {
        "name": "Complex Sentence Test",
        "messages": ["I'm Ana Horvat from Ljubljana, I grow tomatoes"],
        "description": "Should extract multiple pieces of information"
    },
    {
        "name": "Correction Test",
        "messages": ["Petre", "Sorry, I meant Peter"],
        "description": "Should handle corrections"
    },
    {
        "name": "Invalid Phone Test",
        "messages": ["John", "Smith", "123"],
        "description": "Should recognize invalid phone and ask again"
    },
    {
        "name": "Crocodile Test",
        "messages": ["My crocodile ate my mangoes", "Peter"],
        "description": "Should redirect from off-topic to registration"
    },
    {
        "name": "Negation Test",
        "messages": ["My name is not Ljubljana, I'm from there", "Ana Kovač"],
        "description": "Should understand Ljubljana is location, not name"
    },
    {
        "name": "Question Context Test",
        "messages": ["Sisak, you know where that is?", "Yes, that's my farm location"],
        "description": "Should extract Sisak as location from question"
    }
]

async def run_dialogue_test(test_case):
    """Run a single test and return FULL dialogue"""
    
    print(f"\n{'='*70}")
    print(f"TEST: {test_case['name']}")
    print(f"Description: {test_case['description']}")
    print(f"{'='*70}\n")
    
    # Initialize
    llm = await get_llm_registration_engine()
    session_id = f"test_{test_case['name'].replace(' ', '_').lower()}"
    
    # Clear any existing session
    if session_id in registration_sessions:
        del registration_sessions[session_id]
    
    # Store complete dialogue
    dialogue = {
        "test_name": test_case['name'],
        "description": test_case['description'],
        "started_at": datetime.now().isoformat(),
        "exchanges": []
    }
    
    conversation_history = []
    
    # Run through all messages
    for i, message in enumerate(test_case['messages']):
        exchange_num = i + 1
        
        print(f"\n--- Exchange {exchange_num} ---")
        print(f"👤 FARMER: {message}")
        
        # Process message
        try:
            result = await llm.process_registration_message(
                message=message,
                session_id=session_id,
                conversation_history=conversation_history
            )
            
            print(f"🤖 AVA: {result['response']}")
            print(f"📊 EXTRACTED: {json.dumps(result['extracted_data'], indent=2)}")
            print(f"✅ COMPLETE: {result.get('registration_complete', False)}")
            
            missing = result.get('missing_fields', [])
            if missing:
                print(f"❓ MISSING: {', '.join(missing)}")
            
            # Store in dialogue
            dialogue['exchanges'].append({
                "exchange_num": exchange_num,
                "farmer_message": message,
                "ava_response": result['response'],
                "extracted_data": result['extracted_data'],
                "registration_complete": result.get('registration_complete', False),
                "missing_fields": result.get('missing_fields', [])
            })
            
            # Update conversation history
            conversation_history.append({"message": message, "is_farmer": True})
            conversation_history.append({"message": result['response'], "is_farmer": False})
            
            # If registration complete, stop
            if result.get('registration_complete', False):
                print("\n🎉 REGISTRATION COMPLETED!")
                dialogue['completed'] = True
                dialogue['total_exchanges'] = exchange_num
                break
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            dialogue['exchanges'].append({
                "exchange_num": exchange_num,
                "farmer_message": message,
                "error": str(e)
            })
            dialogue['error'] = str(e)
            break
    
    # Final session state
    if session_id in registration_sessions:
        final_data = registration_sessions[session_id].get('collected_data', {})
        print(f"\n📋 FINAL COLLECTED DATA:")
        print(json.dumps(final_data, indent=2))
        dialogue['final_collected_data'] = final_data
    else:
        dialogue['final_collected_data'] = {}
    
    dialogue['ended_at'] = datetime.now().isoformat()
    dialogue['completed'] = dialogue.get('completed', False)
    
    return dialogue

async def run_all_dialogue_tests():
    """Run all tests and save results"""
    
    print("🎭 CAVA REGISTRATION DIALOGUE TESTS - v3.3.6")
    print("=" * 70)
    print("Running complete conversation tests with full visibility\n")
    
    all_dialogues = []
    
    for test_case in DIALOGUE_TEST_CASES:
        dialogue = await run_dialogue_test(test_case)
        all_dialogues.append(dialogue)
        
        # Wait a bit between tests
        await asyncio.sleep(0.5)
    
    # Save all dialogues to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"cava_test_dialogues_{timestamp}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_dialogues, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Full test dialogues saved to: {output_file}")
    
    # Generate HTML report
    generate_html_report(all_dialogues, timestamp)
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    completed_count = 0
    for dialogue in all_dialogues:
        status = "✅ COMPLETED" if dialogue.get('completed') else "❌ INCOMPLETE"
        exchanges = dialogue.get('total_exchanges', len(dialogue['exchanges']))
        print(f"{dialogue['test_name']}: {status} ({exchanges} exchanges)")
        
        if dialogue.get('completed'):
            completed_count += 1
            
        if dialogue.get('error'):
            print(f"  Error: {dialogue['error']}")
            
        # Show final data collected
        final_data = dialogue.get('final_collected_data', {})
        if final_data:
            print(f"  Collected: {', '.join([f'{k}={v}' for k, v in final_data.items() if v])}")
    
    print(f"\n📊 Total: {completed_count}/{len(all_dialogues)} tests completed successfully")
    
    return all_dialogues

def generate_html_report(dialogues, timestamp):
    """Generate readable HTML report of all dialogues"""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>CAVA Test Dialogues - {timestamp}</title>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                margin: 20px;
                background: #f5f5f5;
            }}
            h1 {{
                color: #2e7d32;
                border-bottom: 3px solid #2e7d32;
                padding-bottom: 10px;
            }}
            .test {{ 
                background: white;
                border: 1px solid #ddd; 
                margin: 20px 0; 
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .test h2 {{
                margin-top: 0;
                color: #1976d2;
            }}
            .description {{
                font-style: italic;
                color: #666;
                margin-bottom: 20px;
            }}
            .exchange {{
                margin: 15px 0;
                border-left: 3px solid #ddd;
                padding-left: 15px;
            }}
            .farmer {{ 
                background: #e8f5e9; 
                padding: 10px; 
                margin: 5px 0;
                border-radius: 4px;
                font-weight: bold;
            }}
            .ava {{ 
                background: #f3e5f5; 
                padding: 10px; 
                margin: 5px 0;
                border-radius: 4px;
            }}
            .extracted {{ 
                background: #fff3cd; 
                padding: 10px; 
                margin: 5px 0; 
                font-size: 12px;
                font-family: monospace;
                border-radius: 4px;
            }}
            .error {{ 
                background: #f8d7da; 
                padding: 10px;
                border-radius: 4px;
                color: #721c24;
            }}
            .final-data {{
                background: #d4edda;
                padding: 15px;
                margin-top: 20px;
                border-radius: 4px;
            }}
            .completed {{
                color: #155724;
                font-weight: bold;
            }}
            .incomplete {{
                color: #856404;
                font-weight: bold;
            }}
            .summary {{
                background: white;
                padding: 20px;
                margin: 20px 0;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
        </style>
    </head>
    <body>
        <h1>🎭 CAVA Registration Test Dialogues</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Version: 3.3.6-cava-direct-gpt4</p>
    """
    
    # Summary section
    completed = sum(1 for d in dialogues if d.get('completed'))
    html += f"""
        <div class='summary'>
            <h2>Summary</h2>
            <p>Total Tests: {len(dialogues)}</p>
            <p>Completed: {completed}</p>
            <p>Incomplete: {len(dialogues) - completed}</p>
        </div>
    """
    
    for dialogue in dialogues:
        status_icon = "✅" if dialogue.get('completed') else "❌"
        status_class = "completed" if dialogue.get('completed') else "incomplete"
        
        html += f"<div class='test'>"
        html += f"<h2>{status_icon} {dialogue['test_name']}</h2>"
        html += f"<div class='description'>{dialogue['description']}</div>"
        
        for exchange in dialogue['exchanges']:
            html += f"<div class='exchange'>"
            html += f"<div class='farmer'>👤 FARMER: {exchange['farmer_message']}</div>"
            
            if 'error' in exchange:
                html += f"<div class='error'>❌ ERROR: {exchange['error']}</div>"
            else:
                html += f"<div class='ava'>🤖 AVA: {exchange['ava_response']}</div>"
                
                # Show extracted data if any
                if any(exchange['extracted_data'].values()):
                    extracted_str = json.dumps(exchange['extracted_data'], indent=2)
                    html += f"<div class='extracted'>📊 Extracted: <pre>{extracted_str}</pre></div>"
            
            html += "</div>"
        
        # Show final collected data
        if dialogue.get('final_collected_data'):
            final_str = json.dumps(dialogue['final_collected_data'], indent=2)
            html += f"<div class='final-data'>"
            html += f"<strong>Final Collected Data:</strong>"
            html += f"<pre>{final_str}</pre>"
            html += f"<p class='{status_class}'>Status: {status_icon} "
            html += "Registration Complete" if dialogue.get('completed') else "Registration Incomplete"
            html += "</p>"
            html += "</div>"
        
        html += "</div>"
    
    html += """
    </body>
    </html>
    """
    
    # Save report
    html_file = f'cava_test_report_{timestamp}.html'
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"📄 HTML report saved to: {html_file}")

# Run the tests
if __name__ == "__main__":
    asyncio.run(run_all_dialogue_tests())