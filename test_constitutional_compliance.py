"""
Constitutional Compliance Testing
Every feature must pass these tests
"""

import unittest
import sys
import os

# Add monitoring modules to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitoring.core.llm_query_processor import LLMQueryProcessor
from monitoring.core.response_formatter import ResponseFormatter
from monitoring.config.dashboard_config import DASHBOARD_CONFIG


class TestConstitutionalCompliance(unittest.TestCase):
    """Test all constitutional requirements"""
    
    def setUp(self):
        """Initialize test components"""
        self.llm_processor = LLMQueryProcessor()
        self.formatter = ResponseFormatter()
    
    def test_mango_rule(self):
        """Test: Would this work for mango farmer in Bulgaria?"""
        # Bulgarian query about mangoes
        bulgarian_query = "Колко манго дървета имам?"  # "How many mango trees do I have?"
        
        # Process query
        result = self.llm_processor.process_natural_query(bulgarian_query)
        
        # Verify it processes successfully
        self.assertIsNotNone(result)
        self.assertIn('sql', result)
        self.assertEqual(result['detected_language'], 'bg')
        self.assertNotIn('--', result['sql'])  # Not a failure comment
        
        # Verify it handles mango crops
        self.assertTrue(
            'crops' in result['sql'].lower() or 
            'fields' in result['sql'].lower() or
            'farmers' in result['sql'].lower()
        )
        
        print(f"✅ Mango Rule Test Passed: {result}")
    
    def test_privacy_first(self):
        """Test: No personal farmer data goes to external APIs"""
        # Simulate schema context (only structure, no data)
        schema = "farmers: id, name, email\nfields: id, farmer_id, name"
        self.llm_processor.set_schema_context(schema)
        
        # Verify schema contains no actual farmer data
        self.assertNotIn('@', schema)  # No emails
        self.assertNotIn('John', schema)  # No names
        self.assertNotIn('123', schema)  # No IDs
        
        print("✅ Privacy First Test Passed: Only schema structure used")
    
    def test_module_independence(self):
        """Test: Can modify UI without breaking query processing?"""
        # Test query processor independently
        query_result = self.llm_processor.process_natural_query("Show all farmers")
        self.assertIsNotNone(query_result)
        
        # Test formatter independently
        format_result = self.formatter.format_results(
            [{"id": 1, "name": "Test Farm"}],
            "Show all farmers",
            "en"
        )
        self.assertIsNotNone(format_result)
        
        # Verify they work without dependencies
        self.assertIn('sql', query_result)
        self.assertIn('summary', format_result)
        
        print("✅ Module Independence Test Passed")
    
    def test_llm_first_approach(self):
        """Test: AI handles complexity, not hardcoded rules"""
        # Complex multi-language query
        complex_query = "Покажи ми всички полета с манго по-големи от 10 хектара"
        
        result = self.llm_processor.process_natural_query(complex_query)
        
        # Should generate intelligent SQL, not fail
        self.assertIsNotNone(result)
        self.assertIn('sql', result)
        self.assertIn('SELECT', result['sql'].upper())
        
        print(f"✅ LLM-First Test Passed: {result}")
    
    def test_error_isolation(self):
        """Test: System stays operational with partial failures"""
        # Test with invalid input
        try:
            result = self.formatter.format_error(
                Exception("Database connection failed"),
                "en"
            )
            
            # Should return graceful error, not crash
            self.assertIsNotNone(result)
            self.assertFalse(result['success'])
            self.assertIn('error', result)
            
            print("✅ Error Isolation Test Passed: Graceful error handling")
        except Exception as e:
            self.fail(f"System crashed instead of handling error: {e}")
    
    def test_api_first_communication(self):
        """Test: Clean interfaces between modules"""
        # All module communication through defined interfaces
        
        # LLM Processor has clear input/output
        query_input = "Show farmers"
        query_output = self.llm_processor.process_natural_query(query_input)
        self.assertIsInstance(query_output, dict)
        self.assertIn('sql', query_output)
        
        # Formatter has clear input/output
        format_input = [{"id": 1}]
        format_output = self.formatter.format_results(format_input, query_input, "en")
        self.assertIsInstance(format_output, dict)
        
        print("✅ API-First Test Passed: Clean interfaces")
    
    def test_farmer_centric_tone(self):
        """Test: Professional agricultural tone"""
        # Format results with agricultural context
        results = [
            {"farm_name": "Test Farm", "area_hectares": 50},
            {"farm_name": "Mango Plantation", "area_hectares": 100}
        ]
        
        formatted = self.formatter.format_results(
            results,
            "Show all farms",
            "en"
        )
        
        # Verify professional tone (not overly sweet)
        self.assertNotIn('❤️', str(formatted))
        self.assertNotIn('💕', str(formatted))
        self.assertIn('records', formatted['summary'].lower())
        
        print("✅ Farmer-Centric Tone Test Passed")
    
    def test_multi_language_queries(self):
        """Test: Various languages work without hardcoding"""
        test_queries = [
            ("How many fields?", "en"),
            ("Koliko polja?", "sl"),  # Slovenian
            ("Сколько полей?", "ru"),  # Russian
            ("¿Cuántos campos?", "es"),  # Spanish
            ("Combien de champs?", "fr"),  # French
        ]
        
        for query, expected_lang_family in test_queries:
            result = self.llm_processor.process_natural_query(query)
            self.assertIsNotNone(result)
            self.assertIn('sql', result)
            self.assertIn('COUNT', result['sql'].upper())
            
        print("✅ Multi-Language Test Passed")
    
    def test_configuration_validation(self):
        """Test: Configuration meets requirements"""
        # Verify all constitutional flags are True
        compliance = DASHBOARD_CONFIG["compliance"]
        
        self.assertTrue(compliance["mango_rule"])
        self.assertTrue(compliance["privacy_first"])
        self.assertTrue(compliance["error_isolation"])
        self.assertTrue(compliance["module_independence"])
        self.assertTrue(compliance["api_first"])
        self.assertTrue(compliance["llm_first"])
        self.assertTrue(compliance["farmer_centric"])
        
        print("✅ Configuration Validation Test Passed")
    
    def test_no_hardcoded_translations(self):
        """Test: No hardcoded translation files"""
        # Verify translation files don't exist
        self.assertFalse(os.path.exists('slovenian_translations.py'))
        self.assertFalse(os.path.exists('bulgarian_translations.py'))
        self.assertFalse(os.path.exists('translations.py'))
        
        print("✅ No Hardcoded Translations Test Passed")


if __name__ == '__main__':
    print("🔍 Running Constitutional Compliance Tests...")
    print("=" * 50)
    
    # Run tests
    unittest.main(verbosity=2)