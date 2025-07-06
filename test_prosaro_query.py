"""
Test Croatian Query: "Koliko je karenca za Prosaro u pšenici?"
Verifies the modular architecture works correctly for agricultural queries
"""
import asyncio
import sys
import os
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.llm_router import LLMRouter
from core.language_processor import LanguageProcessor
from core.knowledge_search import KnowledgeSearch
from core.external_search import ExternalSearch

async def test_prosaro_query():
    """Test the Croatian query about Prosaro PHI in wheat"""
    
    # Test query
    query = "Koliko je karenca za Prosaro u pšenici?"
    
    print("🌾 AVA OLO MODULAR ARCHITECTURE TEST")
    print("=" * 50)
    print(f"Test Query: {query}")
    print(f"Expected: Croatian response with PHI information")
    print("=" * 50)
    
    try:
        # Initialize modules
        print("🔧 Initializing modules...")
        router = LLMRouter()
        language_processor = LanguageProcessor()
        knowledge_search = KnowledgeSearch()
        external_search = ExternalSearch()
        
        # Step 1: Language Processing
        print("\n1️⃣ LANGUAGE PROCESSING")
        print("-" * 30)
        processed = await language_processor.process_query(query)
        
        print(f"Detected Language: {processed['language']}")
        print(f"Normalized Query: {processed['normalized_query']}")
        print(f"Intent: {processed['intent']}")
        print(f"Entities: {processed['entities']}")
        
        # Step 2: LLM Routing
        print("\n2️⃣ LLM ROUTING")
        print("-" * 30)
        routing = await router.route_query(query, {"processed_query": processed})
        
        print(f"Query Type: {routing['query_type']}")
        print(f"Data Sources: {routing['data_sources']}")
        print(f"Confidence: {routing['confidence']:.2f}")
        print(f"Reasoning: {routing['reasoning']}")
        
        # Step 3: Knowledge Search
        print("\n3️⃣ KNOWLEDGE SEARCH")
        print("-" * 30)
        
        # Extract chemical and crop from entities
        chemical = processed['entities'].get('chemical', 'Prosaro')
        crop = processed['entities'].get('crop', 'pšenica')
        
        print(f"Searching for: {chemical} in {crop}")
        
        # Search for pesticide information
        pesticide_info = await knowledge_search.search_pesticide_info(chemical, crop)
        
        print(f"Found pesticide info: {pesticide_info['found']}")
        if pesticide_info['found']:
            phi_info = pesticide_info['pesticide_info']
            print(f"PHI Days: {phi_info['phi_days']}")
            print(f"Source: {phi_info['source']}")
        else:
            print(f"Message: {pesticide_info.get('message', 'No specific info found')}")
        
        # Step 4: Fallback to External Search if needed
        if not pesticide_info['found']:
            print("\n4️⃣ EXTERNAL SEARCH (FALLBACK)")
            print("-" * 30)
            external_result = await external_search.search(
                f"{chemical} {crop} PHI karenca safety period", 
                "general"
            )
            
            if external_result['success']:
                print("External search successful")
                print(f"Answer preview: {external_result['answer'][:200]}...")
            else:
                print(f"External search failed: {external_result.get('error', 'Unknown error')}")
        
        # Step 5: Generate Response
        print("\n5️⃣ RESPONSE GENERATION")
        print("-" * 30)
        
        # Combine all information
        answer_data = {
            "query_type": routing['query_type'],
            "chemical": chemical,
            "crop": crop,
            "pesticide_info": pesticide_info,
            "confidence": routing['confidence']
        }
        
        # Generate natural language response
        response = await language_processor.generate_response(
            query,
            answer_data,
            processed['language']
        )
        
        print("Generated Response:")
        print("-" * 20)
        print(response)
        
        # Step 6: Test Results Summary
        print("\n📊 TEST RESULTS SUMMARY")
        print("=" * 50)
        
        success_criteria = {
            "Language Detection": processed['language'] == 'hr',
            "Query Type": routing['query_type'] == 'pest_control',
            "Entity Extraction": bool(processed['entities']),
            "Knowledge Search": pesticide_info['found'] or external_result.get('success', False),
            "Response Generation": bool(response and len(response) > 50)
        }
        
        for criterion, passed in success_criteria.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{criterion}: {status}")
        
        overall_success = all(success_criteria.values())
        print(f"\nOverall Test: {'✅ SUCCESS' if overall_success else '❌ FAILED'}")
        
        if overall_success:
            print("\n🎉 MODULAR ARCHITECTURE TEST COMPLETED SUCCESSFULLY!")
            print("The system correctly:")
            print("- Detected Croatian language")
            print("- Routed to pest control handler")
            print("- Extracted chemical and crop entities")
            print("- Searched agricultural knowledge")
            print("- Generated appropriate response")
        else:
            print("\n⚠️ Some test criteria failed. Check module implementations.")
        
        return overall_success
        
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_module_independence():
    """Test that modules work independently"""
    print("\n🔧 MODULE INDEPENDENCE TEST")
    print("-" * 40)
    
    tests = []
    
    # Test Language Processor independently
    try:
        processor = LanguageProcessor()
        result = await processor.detect_language("Koliko je karenca?")
        tests.append(("Language Processor", result == "hr"))
    except Exception as e:
        tests.append(("Language Processor", False))
        print(f"Language Processor error: {e}")
    
    # Test LLM Router independently
    try:
        router = LLMRouter()
        result = await router.route_query("Prosaro wheat", {})
        tests.append(("LLM Router", "query_type" in result))
    except Exception as e:
        tests.append(("LLM Router", False))
        print(f"LLM Router error: {e}")
    
    # Test Knowledge Search independently
    try:
        knowledge = KnowledgeSearch()
        result = await knowledge.search("Prosaro")
        tests.append(("Knowledge Search", isinstance(result, list)))
    except Exception as e:
        tests.append(("Knowledge Search", False))
        print(f"Knowledge Search error: {e}")
    
    # Test External Search independently
    try:
        external = ExternalSearch()
        health = await external.health_check()
        tests.append(("External Search", health))
    except Exception as e:
        tests.append(("External Search", False))
        print(f"External Search error: {e}")
    
    print("Module Independence Results:")
    for module_name, passed in tests:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {module_name}: {status}")
    
    independence_success = all(result for _, result in tests)
    print(f"\nModule Independence: {'✅ SUCCESS' if independence_success else '❌ FAILED'}")
    
    return independence_success

if __name__ == "__main__":
    async def main():
        print("Starting AVA OLO Modular Architecture Test...")
        
        # Test main functionality
        main_test = await test_prosaro_query()
        
        # Test module independence
        independence_test = await test_module_independence()
        
        print("\n" + "=" * 60)
        print("FINAL TEST RESULTS")
        print("=" * 60)
        print(f"Main Functionality: {'✅ PASS' if main_test else '❌ FAIL'}")
        print(f"Module Independence: {'✅ PASS' if independence_test else '❌ FAIL'}")
        
        if main_test and independence_test:
            print("\n🎉 ALL TESTS PASSED!")
            print("AVA OLO modular architecture is working correctly.")
            print("Ready for Croatian agricultural queries!")
        else:
            print("\n⚠️ Some tests failed. Please check module implementations.")
        
        return main_test and independence_test
    
    # Run the test
    success = asyncio.run(main())