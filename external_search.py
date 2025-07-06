"""
External Search - Perplexity integration for current agricultural information
Handles weather, market prices, news, and current agricultural trends
"""
import logging
from typing import Dict, Any, Optional, List
import httpx
import json
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

logger = logging.getLogger(__name__)

class ExternalSearch:
    """
    External search using Perplexity API
    For current information not in knowledge base
    """
    
    def __init__(self):
        self.api_key = os.getenv('PERPLEXITY_API_KEY')
        self.base_url = "https://api.perplexity.ai"
        self.timeout = 30  # seconds
        
    async def search(self, query: str, search_type: str = "general") -> Dict[str, Any]:
        """
        Search external sources for current information
        
        Args:
            query: Search query (any language)
            search_type: Type of search (general, weather, prices, news)
            
        Returns:
            Search results with sources
        """
        try:
            # Enhance query based on search type
            enhanced_query = self._enhance_query(query, search_type)
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "pplx-70b-online",  # Use online model for current info
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an agricultural assistant providing current information for Croatian farmers. Always cite sources."
                    },
                    {
                        "role": "user",
                        "content": enhanced_query
                    }
                ],
                "temperature": 0.2,  # Lower temperature for factual responses
                "max_tokens": 1000
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Extract and parse response
                    answer = result['choices'][0]['message']['content']
                    
                    return {
                        "success": True,
                        "answer": answer,
                        "search_type": search_type,
                        "sources": self._extract_sources(answer),
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    logger.error(f"Perplexity API error: {response.status_code}")
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code}",
                        "message": "Unable to fetch current information"
                    }
                    
        except Exception as e:
            logger.error(f"External search error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Search service temporarily unavailable"
            }
    
    async def get_weather_forecast(self, location: str, days: int = 7) -> Dict[str, Any]:
        """
        Get weather forecast for agricultural planning
        """
        query = f"Weather forecast for {location} next {days} days for farming agricultural planning temperature rainfall humidity"
        
        result = await self.search(query, "weather")
        
        if result["success"]:
            # Parse weather-specific information
            weather_data = self._parse_weather_response(result["answer"])
            result["weather_data"] = weather_data
        
        return result
    
    async def get_market_prices(self, commodity: str, market: str = "Croatia") -> Dict[str, Any]:
        """
        Get current market prices for agricultural commodities
        """
        query = f"Current {commodity} prices in {market} agricultural market EUR per ton"
        
        result = await self.search(query, "prices")
        
        if result["success"]:
            # Parse price information
            price_data = self._parse_price_response(result["answer"])
            result["price_data"] = price_data
        
        return result
    
    async def get_agricultural_news(self, topic: str = None, region: str = "Croatia") -> Dict[str, Any]:
        """
        Get recent agricultural news and updates
        """
        query = f"Recent agricultural news {region}"
        if topic:
            query += f" about {topic}"
        
        result = await self.search(query, "news")
        
        if result["success"]:
            # Extract news items
            news_items = self._parse_news_response(result["answer"])
            result["news_items"] = news_items
        
        return result
    
    async def get_pest_disease_alerts(self, region: str, crops: List[str]) -> Dict[str, Any]:
        """
        Get current pest and disease alerts for specific crops
        """
        crops_str = ", ".join(crops)
        query = f"Current pest disease alerts warnings {region} for {crops_str} crops"
        
        result = await self.search(query, "alerts")
        
        if result["success"]:
            # Parse alerts
            alerts = self._parse_alerts_response(result["answer"])
            result["alerts"] = alerts
        
        return result
    
    def _enhance_query(self, query: str, search_type: str) -> str:
        """Enhance query based on search type"""
        enhancements = {
            "weather": "Include temperature, rainfall, humidity, wind speed. Provide daily breakdown.",
            "prices": "Include current market prices, price trends, and comparison with previous period.",
            "news": "Include recent developments, policy changes, and market updates.",
            "alerts": "Include severity level, affected areas, and recommended actions.",
            "general": "Provide comprehensive agricultural information with sources."
        }
        
        enhancement = enhancements.get(search_type, enhancements["general"])
        return f"{query}. {enhancement}"
    
    def _extract_sources(self, answer: str) -> List[str]:
        """Extract sources from answer text"""
        sources = []
        
        # Look for common source patterns
        # This is simplified - Perplexity usually includes sources in a specific format
        lines = answer.split('\n')
        for line in lines:
            if 'http' in line or 'www.' in line:
                # Extract URL
                import re
                urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', line)
                sources.extend(urls)
        
        return list(set(sources))  # Remove duplicates
    
    def _parse_weather_response(self, answer: str) -> Dict[str, Any]:
        """Parse weather information from response"""
        # This would use more sophisticated parsing in production
        # For now, return structured placeholder
        return {
            "summary": "Weather data extracted from response",
            "forecast": [],
            "agricultural_impact": "Suitable for most farming activities"
        }
    
    def _parse_price_response(self, answer: str) -> Dict[str, Any]:
        """Parse price information from response"""
        return {
            "commodity": "",
            "current_price": 0,
            "currency": "EUR",
            "unit": "ton",
            "trend": "stable",
            "last_updated": datetime.now().isoformat()
        }
    
    def _parse_news_response(self, answer: str) -> List[Dict[str, str]]:
        """Parse news items from response"""
        return [
            {
                "title": "Agricultural news item",
                "summary": "News summary",
                "relevance": "high"
            }
        ]
    
    def _parse_alerts_response(self, answer: str) -> List[Dict[str, Any]]:
        """Parse pest/disease alerts from response"""
        return [
            {
                "type": "pest",
                "name": "Alert name",
                "severity": "medium",
                "affected_crops": [],
                "recommended_action": "Monitor fields"
            }
        ]
    
    async def health_check(self) -> bool:
        """Check if external search service is available"""
        try:
            # Simple API check
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=headers
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"External search health check failed: {str(e)}")
            return False