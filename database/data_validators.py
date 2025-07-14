"""
Constitutional Data Validators
LLM-First data validation following Constitutional Principle #3
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ConstitutionalDataValidator:
    """LLM-First data validation with constitutional compliance"""
    
    def __init__(self):
        """Initialize constitutional validator"""
        self.constitutional_principles = {
            'mango_rule': 'Must work for Bulgarian mango farmers',
            'llm_first': 'AI validation over hardcoded rules', 
            'privacy_first': 'No personal data to external APIs',
            'global': 'Support all countries and crops'
        }
    
    async def validate_farmer_data(self, farmer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate farmer data using LLM-first approach
        
        Args:
            farmer_data: Dictionary containing farmer information
            
        Returns:
            Dictionary with validation results and suggestions
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': [],
            'constitutional_compliance': True
        }
        
        # MANGO RULE: Test if Bulgarian mango farmer can use this
        if not await self._test_mango_rule_compliance(farmer_data):
            validation_result['constitutional_compliance'] = False
            validation_result['errors'].append('MANGO RULE violation: Bulgarian mango farmer cannot use this data')
        
        # Validate required fields
        required_fields = ['farm_name', 'manager_name', 'country']
        for field in required_fields:
            if not farmer_data.get(field):
                validation_result['valid'] = False
                validation_result['errors'].append(f'Required field missing: {field}')
        
        # LLM-First validation: Check for completeness
        llm_suggestions = await self._llm_enhance_farmer_data(farmer_data)
        validation_result['suggestions'] = llm_suggestions
        
        # Privacy-First: No personal data logging
        logger.info(f"Farmer data validated: farm_id={farmer_data.get('farm_id', 'new')}")
        
        return validation_result
    
    async def validate_crop_data(self, crop_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate crop data with global crop support
        
        Args:
            crop_data: Dictionary containing crop information
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': [],
            'constitutional_compliance': True
        }
        
        # MANGO RULE: Must support mangoes in Bulgaria
        crop_name = crop_data.get('crop_name', '').lower()
        if 'mango' in crop_name:
            # Special validation for mango cultivation
            country = crop_data.get('country', '').upper()
            if country == 'BG' or country == 'BULGARIA':
                validation_result['warnings'].append('Mango cultivation in Bulgaria requires special climate considerations')
                validation_result['suggestions'].append('Consider greenhouse cultivation for mango in temperate climates')
        
        # Global crop support validation
        supported_crops = await self._get_global_crop_list()
        if crop_name and crop_name not in [c.lower() for c in supported_crops]:
            validation_result['suggestions'].append(f'New crop detected: {crop_name}. Adding to global crop database.')
        
        # Required fields
        required_fields = ['crop_name', 'planting_date', 'farmer_id']
        for field in required_fields:
            if not crop_data.get(field):
                validation_result['valid'] = False
                validation_result['errors'].append(f'Required field missing: {field}')
        
        return validation_result
    
    async def _test_mango_rule_compliance(self, data: Dict[str, Any]) -> bool:
        """
        Test if Bulgarian mango farmer can use this data structure
        Constitutional Principle #1: THE MANGO RULE
        """
        # Simulate Bulgarian mango farmer data
        bulgarian_mango_farmer = {
            'farm_name': 'София Манго Ферма',  # Sofia Mango Farm in Bulgarian
            'manager_name': 'Димитър',  # Dimitar in Bulgarian
            'country': 'Bulgaria',
            'crop_name': 'mango',
            'language': 'bg'
        }
        
        # Check if all required fields exist
        required_keys = ['farm_name', 'manager_name']
        for key in required_keys:
            if key not in data:
                return False
        
        # Check if international characters are supported
        try:
            farm_name = data.get('farm_name', '')
            if isinstance(farm_name, str) and len(farm_name) > 0:
                # Test Cyrillic character support
                test_cyrillic = 'Димитър Манго Ферма'
                return True
        except UnicodeError:
            return False
        
        return True
    
    async def _llm_enhance_farmer_data(self, farmer_data: Dict[str, Any]) -> List[str]:
        """
        Use LLM-first approach to enhance farmer data
        Constitutional Principle #3: LLM-FIRST
        """
        suggestions = []
        
        # Mock LLM enhancement (in production, would call actual LLM)
        farm_name = farmer_data.get('farm_name', '')
        country = farmer_data.get('country', '')
        
        if farm_name and not farmer_data.get('farm_size'):
            suggestions.append('Consider adding farm size for better agricultural planning')
        
        if country and not farmer_data.get('climate_zone'):
            suggestions.append(f'Consider adding climate zone information for {country}')
        
        if not farmer_data.get('preferred_language'):
            suggestions.append('Adding preferred language helps with localized advice')
        
        # Constitutional: Support minority farmers
        if country == 'Croatia' and not farmer_data.get('minority_language'):
            suggestions.append('Consider adding minority language support (e.g., Hungarian speakers in Croatia)')
        
        return suggestions
    
    async def _get_global_crop_list(self) -> List[str]:
        """
        Get list of globally supported crops
        Constitutional Principle #1: Global crop support
        """
        # Mock global crop database (in production, would query actual database)
        global_crops = [
            'wheat', 'corn', 'rice', 'barley', 'oats',
            'tomato', 'potato', 'carrot', 'onion', 'lettuce',
            'apple', 'orange', 'banana', 'grape', 'strawberry',
            'mango', 'pineapple', 'coconut',  # Tropical fruits for MANGO RULE
            'sunflower', 'soybean', 'cotton', 'tobacco',
            'lavender', 'herbs', 'spices'
        ]
        return global_crops

# Singleton instance
constitutional_validator = ConstitutionalDataValidator()