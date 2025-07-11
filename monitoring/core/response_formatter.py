"""
CONSTITUTIONAL COMPLIANCE: FARMER-CENTRIC + LLM-FIRST
Response formatting using LLM intelligence
"""

import json
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class ResponseFormatter:
    """Format database results using LLM intelligence"""
    
    def format_results(self, sql_results: List[Dict], original_query: str, detected_language: str) -> Dict[str, Any]:
        """
        Constitutional: LLM formats response appropriately
        Professional agricultural tone, user's language
        
        Args:
            sql_results: Database query results
            original_query: Original user query
            detected_language: Auto-detected language
            
        Returns:
            Formatted response appropriate for agricultural context
        """
        
        # Build LLM prompt for formatting
        llm_prompt = f"""Format database results for agricultural professional.

Original Query: {original_query}
Language: {detected_language}
Result Count: {len(sql_results)}

Instructions:
1. Use professional agricultural terminology
2. Format in the detected language
3. Summarize key findings clearly
4. Include relevant agricultural context
5. NO overly sweet tone - professional and direct

Return JSON:
{{
    "summary": "Brief summary in user's language",
    "key_findings": ["finding1", "finding2"],
    "formatted_data": "Human-readable format",
    "recommendations": "Any agricultural recommendations"
}}
"""
        
        # Process with intelligence
        return self._format_intelligently(sql_results, original_query, detected_language)
    
    def format_table_view(self, table_data: Dict[str, Any], table_name: str, language: str) -> Dict[str, Any]:
        """Format table data for display"""
        return {
            "table_name": table_name,
            "row_count": len(table_data.get('rows', [])),
            "columns": table_data.get('columns', []),
            "data": table_data.get('rows', []),
            "language": language
        }
    
    def format_modification_result(self, result: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Format modification operation results"""
        success = result.get('success', False)
        operation = result.get('operation', 'unknown')
        
        # Generate message in detected language
        if language == 'bg':
            status_msg = 'Успешно' if success else 'Неуспешно'
            operation_msgs = {
                'insert': 'добавяне на запис',
                'update': 'актуализиране на запис',
                'delete': 'изтриване на запис'
            }
        elif language == 'sl':
            status_msg = 'Uspešno' if success else 'Neuspešno'
            operation_msgs = {
                'insert': 'dodajanje zapisa',
                'update': 'posodabljanje zapisa',
                'delete': 'brisanje zapisa'
            }
        else:
            status_msg = 'Successful' if success else 'Failed'
            operation_msgs = {
                'insert': 'record insertion',
                'update': 'record update',
                'delete': 'record deletion'
            }
        
        return {
            "success": success,
            "message": f"{status_msg} {operation_msgs.get(operation, operation)}",
            "details": result,
            "language": language
        }
    
    def format_error(self, error: Exception, language: str) -> Dict[str, Any]:
        """Format error messages professionally"""
        # Error messages in different languages
        error_messages = {
            'en': {
                'general': 'An error occurred while processing your request',
                'connection': 'Database connection temporarily unavailable',
                'invalid': 'Invalid query format',
                'permission': 'Insufficient permissions for this operation'
            },
            'bg': {
                'general': 'Възникна грешка при обработката на заявката',
                'connection': 'Връзката с базата данни временно не е налична',
                'invalid': 'Невалиден формат на заявката',
                'permission': 'Недостатъчни права за тази операция'
            },
            'sl': {
                'general': 'Pri obdelavi zahteve je prišlo do napake',
                'connection': 'Povezava z bazo podatkov trenutno ni na voljo',
                'invalid': 'Neveljavna oblika poizvedbe',
                'permission': 'Nezadostne pravice za to operacijo'
            }
        }
        
        # Determine error type
        error_str = str(error).lower()
        if 'connection' in error_str or 'connect' in error_str:
            error_type = 'connection'
        elif 'permission' in error_str or 'denied' in error_str:
            error_type = 'permission'
        elif 'invalid' in error_str or 'syntax' in error_str:
            error_type = 'invalid'
        else:
            error_type = 'general'
        
        lang_errors = error_messages.get(language, error_messages['en'])
        
        return {
            "success": False,
            "error": lang_errors.get(error_type, lang_errors['general']),
            "error_type": error_type,
            "technical_details": str(error) if logger.level <= logging.DEBUG else None
        }
    
    def _format_intelligently(self, results: List[Dict], query: str, language: str) -> Dict[str, Any]:
        """
        Intelligent formatting based on query context and results
        Works for any agricultural data in any language
        """
        if not results:
            return self._format_empty_results(language)
        
        # Analyze result structure
        result_count = len(results)
        
        # Check if it's a count query
        if result_count == 1 and 'count' in results[0]:
            return self._format_count_results(results[0]['count'], query, language)
        
        # Format based on detected language
        if language == 'bg':
            summary = f"Намерени {result_count} записа"
            if 'манго' in query.lower():
                summary += " за манго култури"
        elif language == 'sl':
            summary = f"Najdenih {result_count} zapisov"
        else:
            summary = f"Found {result_count} records"
        
        # Extract key findings
        key_findings = []
        if result_count > 0:
            # Analyze first few records for patterns
            sample = results[:5]
            for record in sample:
                if 'farm_name' in record:
                    key_findings.append(f"Farm: {record['farm_name']}")
                elif 'name' in record and 'area_hectares' in record:
                    key_findings.append(f"Field: {record['name']} ({record['area_hectares']} ha)")
        
        return {
            "summary": summary,
            "key_findings": key_findings[:3],
            "total_count": result_count,
            "data": results,
            "language": language
        }
    
    def _format_count_results(self, count: int, query: str, language: str) -> Dict[str, Any]:
        """Format count query results"""
        if language == 'bg':
            if 'манго' in query.lower():
                summary = f"Общ брой манго дървета: {count}"
            else:
                summary = f"Общ брой: {count}"
        elif language == 'sl':
            summary = f"Skupno število: {count}"
        else:
            summary = f"Total count: {count}"
        
        return {
            "summary": summary,
            "count": count,
            "language": language
        }
    
    def _format_empty_results(self, language: str) -> Dict[str, Any]:
        """Format empty result set"""
        messages = {
            'bg': 'Няма намерени записи',
            'sl': 'Ni najdenih zapisov',
            'en': 'No records found'
        }
        
        return {
            "summary": messages.get(language, messages['en']),
            "data": [],
            "total_count": 0,
            "language": language
        }