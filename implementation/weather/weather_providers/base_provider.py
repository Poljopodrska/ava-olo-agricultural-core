#!/usr/bin/env python3
"""
Base Weather Provider
Constitutional abstract base class for all weather providers
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime, date
import logging
import aiohttp
import asyncio
from decimal import Decimal

logger = logging.getLogger(__name__)

class WeatherProviderError(Exception):
    """Base exception for weather provider errors"""
    pass

class WeatherProviderRateLimitError(WeatherProviderError):
    """Rate limit exceeded error"""
    pass

class WeatherProviderAuthError(WeatherProviderError):
    """Authentication error"""
    pass

class WeatherProviderDataError(WeatherProviderError):
    """Data quality or parsing error"""
    pass

class BaseWeatherProvider(ABC):
    """
    Constitutional Base Weather Provider
    
    Abstract base class that all weather providers must implement
    to ensure constitutional compliance and consistent behavior.
    """
    
    def __init__(self, provider_config: Dict[str, Any]):
        """
        Initialize the weather provider
        
        Args:
            provider_config: Provider configuration dictionary
        """
        self.provider_config = provider_config
        self.provider_name = provider_config.get('name', 'unknown')
        self.api_base_url = provider_config.get('api_base_url', '')
        self.api_version = provider_config.get('api_version', '')
        self.api_key = self._get_api_key(provider_config.get('api_key_env_var'))
        self.config = provider_config.get('config', {})
        
        # Rate limiting
        self.max_requests_per_minute = provider_config.get('max_requests_per_minute', 60)
        self.request_count = 0
        self.last_reset_time = datetime.now()
        
        # Constitutional compliance
        self.constitutional_compliance_score = provider_config.get('compliance_score', 0)
        self.mango_rule_verified = provider_config.get('mango_rule_verified', False)
        
        # HTTP session
        self.session = None
        
        logger.info(f"🏛️ {self.provider_name} weather provider initialized")
    
    def _get_api_key(self, env_var: str) -> Optional[str]:
        """Get API key from environment variable"""
        import os
        if env_var:
            return os.getenv(env_var)
        return None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def get_current_weather(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Get current weather conditions
        
        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            
        Returns:
            Dictionary containing current weather data
        """
        pass
    
    @abstractmethod
    async def get_weather_forecast(self, latitude: float, longitude: float, 
                                 days: int = 7) -> List[Dict[str, Any]]:
        """
        Get weather forecast
        
        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            days: Number of days to forecast
            
        Returns:
            List of weather forecast data
        """
        pass
    
    @abstractmethod
    async def get_historical_weather(self, latitude: float, longitude: float,
                                   start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        Get historical weather data
        
        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            start_date: Start date for historical data
            end_date: End date for historical data
            
        Returns:
            List of historical weather data
        """
        pass
    
    def check_rate_limit(self) -> bool:
        """Check if rate limit allows another request"""
        now = datetime.now()
        
        # Reset counter if a minute has passed
        if (now - self.last_reset_time).total_seconds() >= 60:
            self.request_count = 0
            self.last_reset_time = now
        
        # Check if we can make another request
        if self.request_count >= self.max_requests_per_minute:
            return False
        
        self.request_count += 1
        return True
    
    async def make_request(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make HTTP request with rate limiting and error handling
        
        Args:
            url: API endpoint URL
            params: Query parameters
            
        Returns:
            Response data as dictionary
        """
        # Check rate limit
        if not self.check_rate_limit():
            raise WeatherProviderRateLimitError(
                f"Rate limit exceeded for {self.provider_name}"
            )
        
        # Add API key to parameters
        if self.api_key:
            params = params or {}
            params['appid'] = self.api_key  # Common for many providers
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(url, params=params) as response:
                if response.status == 401:
                    raise WeatherProviderAuthError(
                        f"Authentication failed for {self.provider_name}"
                    )
                elif response.status == 429:
                    raise WeatherProviderRateLimitError(
                        f"Rate limit exceeded for {self.provider_name}"
                    )
                elif response.status != 200:
                    raise WeatherProviderError(
                        f"API request failed with status {response.status}"
                    )
                
                data = await response.json()
                return data
                
        except aiohttp.ClientError as e:
            raise WeatherProviderError(f"Network error: {e}")
        except Exception as e:
            raise WeatherProviderError(f"Unexpected error: {e}")
    
    def standardize_weather_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standardize weather data to constitutional format
        
        Args:
            raw_data: Raw weather data from provider
            
        Returns:
            Standardized weather data
        """
        # Base structure - subclasses should override
        return {
            'date': datetime.now().date(),
            'temperature': self._safe_decimal(raw_data.get('temperature')),
            'temperature_min': self._safe_decimal(raw_data.get('temperature_min')),
            'temperature_max': self._safe_decimal(raw_data.get('temperature_max')),
            'humidity': self._safe_decimal(raw_data.get('humidity')),
            'rainfall': self._safe_decimal(raw_data.get('rainfall', 0)),
            'wind_speed': self._safe_decimal(raw_data.get('wind_speed')),
            'wind_direction': raw_data.get('wind_direction'),
            'pressure': self._safe_decimal(raw_data.get('pressure')),
            'condition': raw_data.get('condition', 'unknown'),
            'description': raw_data.get('description', ''),
            'icon': raw_data.get('icon', ''),
            'provider': self.provider_name,
            'raw_data': raw_data
        }
    
    def _safe_decimal(self, value: Any) -> Optional[Decimal]:
        """Safely convert value to Decimal"""
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return None
    
    def _celsius_to_fahrenheit(self, celsius: float) -> float:
        """Convert Celsius to Fahrenheit"""
        return (celsius * 9/5) + 32
    
    def _fahrenheit_to_celsius(self, fahrenheit: float) -> float:
        """Convert Fahrenheit to Celsius"""
        return (fahrenheit - 32) * 5/9
    
    def _meters_per_second_to_kmh(self, mps: float) -> float:
        """Convert meters per second to km/h"""
        return mps * 3.6
    
    def _kmh_to_mph(self, kmh: float) -> float:
        """Convert km/h to mph"""
        return kmh * 0.621371
    
    def _mm_to_inches(self, mm: float) -> float:
        """Convert mm to inches"""
        return mm * 0.0393701
    
    def validate_coordinates(self, latitude: float, longitude: float) -> bool:
        """
        Validate latitude and longitude coordinates
        
        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            
        Returns:
            True if coordinates are valid
        """
        return (-90 <= latitude <= 90) and (-180 <= longitude <= 180)
    
    def is_mango_compatible(self, weather_data: Dict[str, Any]) -> bool:
        """
        Check if weather conditions are suitable for mango growing
        (MANGO RULE compliance check)
        
        Args:
            weather_data: Weather data dictionary
            
        Returns:
            True if conditions are mango-suitable
        """
        temp = weather_data.get('temperature')
        humidity = weather_data.get('humidity')
        
        if not temp or not humidity:
            return False
        
        # Mango growing conditions:
        # Temperature: 20-30°C optimal
        # Humidity: 50-80% optimal
        temp_suitable = 15 <= float(temp) <= 35
        humidity_suitable = 40 <= float(humidity) <= 90
        
        return temp_suitable and humidity_suitable
    
    async def test_provider_connection(self) -> bool:
        """
        Test provider connection and API key validity
        
        Returns:
            True if connection is successful
        """
        try:
            # Test with a known location (Sofia, Bulgaria for MANGO RULE)
            test_data = await self.get_current_weather(42.6977, 23.3219)
            return test_data is not None
            
        except Exception as e:
            logger.error(f"❌ Provider connection test failed: {e}")
            return False
    
    def get_constitutional_compliance_score(self) -> int:
        """Get constitutional compliance score"""
        return self.constitutional_compliance_score
    
    def is_mango_rule_verified(self) -> bool:
        """Check if provider is MANGO RULE verified"""
        return self.mango_rule_verified
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information"""
        return {
            'name': self.provider_name,
            'api_base_url': self.api_base_url,
            'api_version': self.api_version,
            'constitutional_compliance_score': self.constitutional_compliance_score,
            'mango_rule_verified': self.mango_rule_verified,
            'max_requests_per_minute': self.max_requests_per_minute,
            'current_request_count': self.request_count
        }