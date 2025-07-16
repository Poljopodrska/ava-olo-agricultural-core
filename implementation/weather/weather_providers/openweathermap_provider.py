#!/usr/bin/env python3
"""
OpenWeatherMap Provider
Constitutional OpenWeatherMap API integration
"""

import os
import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal
import aiohttp

from .base_provider import BaseWeatherProvider, WeatherProviderError, WeatherProviderDataError

logger = logging.getLogger(__name__)

class OpenWeatherMapProvider(BaseWeatherProvider):
    """
    Constitutional OpenWeatherMap Provider
    
    Integrates with OpenWeatherMap API while maintaining constitutional
    compliance and providing standardized weather data.
    """
    
    def __init__(self, provider_config: Dict[str, Any]):
        """Initialize OpenWeatherMap provider"""
        super().__init__(provider_config)
        
        # OpenWeatherMap specific configuration
        self.api_base_url = provider_config.get('api_base_url', 'https://api.openweathermap.org/data/2.5')
        self.api_key = os.getenv('OPENWEATHERMAP_API_KEY')
        
        if not self.api_key:
            logger.warning("⚠️ OpenWeatherMap API key not found in environment")
        
        # API endpoints
        self.endpoints = {
            'current': f"{self.api_base_url}/weather",
            'forecast': f"{self.api_base_url}/forecast",
            'onecall': f"{self.api_base_url}/onecall",
            'history': f"{self.api_base_url}/onecall/timemachine"
        }
        
        # Units: metric (Celsius, m/s, mm), imperial (Fahrenheit, mph, inches), kelvin
        self.units = 'metric'
        
        logger.info("🏛️ OpenWeatherMap provider initialized")
    
    async def get_current_weather(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Get current weather from OpenWeatherMap
        
        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            
        Returns:
            Current weather data
        """
        try:
            if not self.validate_coordinates(latitude, longitude):
                raise WeatherProviderError("Invalid coordinates")
            
            params = {
                'lat': latitude,
                'lon': longitude,
                'units': self.units,
                'appid': self.api_key
            }
            
            raw_data = await self.make_request(self.endpoints['current'], params)
            
            if not raw_data:
                raise WeatherProviderDataError("No current weather data received")
            
            # Parse and standardize OpenWeatherMap current weather response
            standardized_data = self._parse_current_weather(raw_data)
            
            # Validate mango compatibility (MANGO RULE)
            standardized_data['mango_compatible'] = self.is_mango_compatible(standardized_data)
            
            return standardized_data
            
        except Exception as e:
            logger.error(f"❌ Error getting current weather: {e}")
            raise WeatherProviderError(f"Failed to get current weather: {e}")
    
    async def get_weather_forecast(self, latitude: float, longitude: float, 
                                 days: int = 7) -> List[Dict[str, Any]]:
        """
        Get weather forecast from OpenWeatherMap
        
        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            days: Number of days to forecast (max 5 for free tier)
            
        Returns:
            List of forecast data
        """
        try:
            if not self.validate_coordinates(latitude, longitude):
                raise WeatherProviderError("Invalid coordinates")
            
            # OpenWeatherMap free tier provides 5-day forecast
            if days > 5:
                logger.warning(f"⚠️ OpenWeatherMap free tier limited to 5 days, requested {days}")
                days = 5
            
            params = {
                'lat': latitude,
                'lon': longitude,
                'units': self.units,
                'appid': self.api_key
            }
            
            raw_data = await self.make_request(self.endpoints['forecast'], params)
            
            if not raw_data or 'list' not in raw_data:
                raise WeatherProviderDataError("No forecast data received")
            
            # Parse OpenWeatherMap forecast response
            forecast_data = self._parse_forecast_data(raw_data, days)
            
            # Add mango compatibility to each forecast item
            for item in forecast_data:
                item['mango_compatible'] = self.is_mango_compatible(item)
            
            return forecast_data
            
        except Exception as e:
            logger.error(f"❌ Error getting weather forecast: {e}")
            raise WeatherProviderError(f"Failed to get weather forecast: {e}")
    
    async def get_historical_weather(self, latitude: float, longitude: float,
                                   start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        Get historical weather data from OpenWeatherMap
        
        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            start_date: Start date for historical data
            end_date: End date for historical data
            
        Returns:
            List of historical weather data
        """
        try:
            if not self.validate_coordinates(latitude, longitude):
                raise WeatherProviderError("Invalid coordinates")
            
            # OpenWeatherMap historical data requires One Call API (paid)
            logger.warning("⚠️ Historical weather data requires OpenWeatherMap One Call API subscription")
            
            historical_data = []
            current_date = start_date
            
            while current_date <= end_date:
                # Convert date to Unix timestamp
                timestamp = int(datetime.combine(current_date, datetime.min.time()).timestamp())
                
                params = {
                    'lat': latitude,
                    'lon': longitude,
                    'dt': timestamp,
                    'units': self.units,
                    'appid': self.api_key
                }
                
                try:
                    raw_data = await self.make_request(self.endpoints['history'], params)
                    
                    if raw_data and 'current' in raw_data:
                        historical_item = self._parse_historical_data(raw_data, current_date)
                        historical_item['mango_compatible'] = self.is_mango_compatible(historical_item)
                        historical_data.append(historical_item)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to get historical data for {current_date}: {e}")
                
                current_date += timedelta(days=1)
            
            return historical_data
            
        except Exception as e:
            logger.error(f"❌ Error getting historical weather: {e}")
            raise WeatherProviderError(f"Failed to get historical weather: {e}")
    
    def _parse_current_weather(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse OpenWeatherMap current weather response"""
        try:
            main = raw_data.get('main', {})
            weather = raw_data.get('weather', [{}])[0]
            wind = raw_data.get('wind', {})
            
            return {
                'date': datetime.now().date(),
                'datetime': datetime.now(),
                'temperature': self._safe_decimal(main.get('temp')),
                'temperature_min': self._safe_decimal(main.get('temp_min')),
                'temperature_max': self._safe_decimal(main.get('temp_max')),
                'temperature_feels_like': self._safe_decimal(main.get('feels_like')),
                'humidity': self._safe_decimal(main.get('humidity')),
                'pressure': self._safe_decimal(main.get('pressure')),
                'visibility': self._safe_decimal(raw_data.get('visibility', 0) / 1000),  # Convert to km
                'wind_speed': self._safe_decimal(wind.get('speed')),
                'wind_direction': wind.get('deg'),
                'wind_gust': self._safe_decimal(wind.get('gust')),
                'cloud_cover': self._safe_decimal(raw_data.get('clouds', {}).get('all')),
                'condition': weather.get('main', 'unknown').lower(),
                'description': weather.get('description', ''),
                'icon': weather.get('icon', ''),
                'rainfall': self._safe_decimal(raw_data.get('rain', {}).get('1h', 0)),
                'snowfall': self._safe_decimal(raw_data.get('snow', {}).get('1h', 0)),
                'sunrise': datetime.fromtimestamp(raw_data.get('sys', {}).get('sunrise', 0)),
                'sunset': datetime.fromtimestamp(raw_data.get('sys', {}).get('sunset', 0)),
                'provider': 'openweathermap',
                'data_quality_score': self._assess_data_quality(raw_data),
                'raw_data': raw_data
            }
            
        except Exception as e:
            logger.error(f"❌ Error parsing current weather data: {e}")
            raise WeatherProviderDataError(f"Failed to parse current weather: {e}")
    
    def _parse_forecast_data(self, raw_data: Dict[str, Any], days: int) -> List[Dict[str, Any]]:
        """Parse OpenWeatherMap forecast response"""
        try:
            forecast_list = raw_data.get('list', [])
            forecast_data = []
            
            # Group forecast items by date
            daily_forecasts = {}
            
            for item in forecast_list:
                # Parse datetime
                dt = datetime.fromtimestamp(item.get('dt', 0))
                date_key = dt.date()
                
                # Skip if we have enough days
                if len(daily_forecasts) >= days:
                    break
                
                # Parse weather data
                main = item.get('main', {})
                weather = item.get('weather', [{}])[0]
                wind = item.get('wind', {})
                
                forecast_item = {
                    'date': date_key,
                    'datetime': dt,
                    'hour': dt.hour,
                    'temperature': self._safe_decimal(main.get('temp')),
                    'temperature_min': self._safe_decimal(main.get('temp_min')),
                    'temperature_max': self._safe_decimal(main.get('temp_max')),
                    'temperature_feels_like': self._safe_decimal(main.get('feels_like')),
                    'humidity': self._safe_decimal(main.get('humidity')),
                    'pressure': self._safe_decimal(main.get('pressure')),
                    'wind_speed': self._safe_decimal(wind.get('speed')),
                    'wind_direction': wind.get('deg'),
                    'wind_gust': self._safe_decimal(wind.get('gust')),
                    'cloud_cover': self._safe_decimal(item.get('clouds', {}).get('all')),
                    'condition': weather.get('main', 'unknown').lower(),
                    'description': weather.get('description', ''),
                    'icon': weather.get('icon', ''),
                    'rainfall': self._safe_decimal(item.get('rain', {}).get('3h', 0)),
                    'snowfall': self._safe_decimal(item.get('snow', {}).get('3h', 0)),
                    'rainfall_probability': self._safe_decimal(item.get('pop', 0) * 100),
                    'provider': 'openweathermap',
                    'data_quality_score': self._assess_data_quality(item),
                    'raw_data': item
                }
                
                # Group by date for daily aggregation
                if date_key not in daily_forecasts:
                    daily_forecasts[date_key] = []
                daily_forecasts[date_key].append(forecast_item)
            
            # Create daily aggregated forecasts
            for date_key in sorted(daily_forecasts.keys())[:days]:
                daily_items = daily_forecasts[date_key]
                
                # Aggregate daily data
                daily_forecast = self._aggregate_daily_forecast(daily_items)
                daily_forecast['date'] = date_key
                daily_forecast['hourly_data'] = daily_items
                
                forecast_data.append(daily_forecast)
            
            return forecast_data
            
        except Exception as e:
            logger.error(f"❌ Error parsing forecast data: {e}")
            raise WeatherProviderDataError(f"Failed to parse forecast: {e}")
    
    def _aggregate_daily_forecast(self, hourly_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate hourly forecast data into daily forecast"""
        try:
            if not hourly_items:
                return {}
            
            # Calculate daily aggregates
            temperatures = [float(item['temperature']) for item in hourly_items if item['temperature']]
            temp_mins = [float(item['temperature_min']) for item in hourly_items if item['temperature_min']]
            temp_maxs = [float(item['temperature_max']) for item in hourly_items if item['temperature_max']]
            humidities = [float(item['humidity']) for item in hourly_items if item['humidity']]
            wind_speeds = [float(item['wind_speed']) for item in hourly_items if item['wind_speed']]
            rainfalls = [float(item['rainfall']) for item in hourly_items if item['rainfall']]
            
            # Find most common condition
            conditions = [item['condition'] for item in hourly_items if item['condition']]
            most_common_condition = max(set(conditions), key=conditions.count) if conditions else 'unknown'
            
            # Find representative icon (midday if available)
            midday_item = None
            for item in hourly_items:
                if item['hour'] == 12:  # Noon
                    midday_item = item
                    break
            
            if not midday_item:
                midday_item = hourly_items[len(hourly_items) // 2]  # Middle item
            
            return {
                'temperature': self._safe_decimal(sum(temperatures) / len(temperatures) if temperatures else 0),
                'temperature_min': self._safe_decimal(min(temp_mins) if temp_mins else 0),
                'temperature_max': self._safe_decimal(max(temp_maxs) if temp_maxs else 0),
                'humidity': self._safe_decimal(sum(humidities) / len(humidities) if humidities else 0),
                'wind_speed': self._safe_decimal(sum(wind_speeds) / len(wind_speeds) if wind_speeds else 0),
                'rainfall': self._safe_decimal(sum(rainfalls) if rainfalls else 0),
                'condition': most_common_condition,
                'description': midday_item.get('description', ''),
                'icon': midday_item.get('icon', ''),
                'provider': 'openweathermap',
                'data_quality_score': max(item['data_quality_score'] for item in hourly_items)
            }
            
        except Exception as e:
            logger.error(f"❌ Error aggregating daily forecast: {e}")
            return {}
    
    def _parse_historical_data(self, raw_data: Dict[str, Any], target_date: date) -> Dict[str, Any]:
        """Parse OpenWeatherMap historical data response"""
        try:
            current = raw_data.get('current', {})
            weather = current.get('weather', [{}])[0]
            
            return {
                'date': target_date,
                'datetime': datetime.combine(target_date, datetime.min.time()),
                'temperature': self._safe_decimal(current.get('temp')),
                'temperature_feels_like': self._safe_decimal(current.get('feels_like')),
                'humidity': self._safe_decimal(current.get('humidity')),
                'pressure': self._safe_decimal(current.get('pressure')),
                'wind_speed': self._safe_decimal(current.get('wind_speed')),
                'wind_direction': current.get('wind_deg'),
                'cloud_cover': self._safe_decimal(current.get('clouds')),
                'condition': weather.get('main', 'unknown').lower(),
                'description': weather.get('description', ''),
                'icon': weather.get('icon', ''),
                'rainfall': self._safe_decimal(current.get('rain', {}).get('1h', 0)),
                'snowfall': self._safe_decimal(current.get('snow', {}).get('1h', 0)),
                'uv_index': self._safe_decimal(current.get('uvi')),
                'provider': 'openweathermap',
                'data_quality_score': self._assess_data_quality(raw_data),
                'raw_data': raw_data
            }
            
        except Exception as e:
            logger.error(f"❌ Error parsing historical data: {e}")
            raise WeatherProviderDataError(f"Failed to parse historical data: {e}")
    
    def _assess_data_quality(self, raw_data: Dict[str, Any]) -> int:
        """Assess data quality score (0-100)"""
        try:
            score = 100
            
            # Check for missing essential data
            if 'main' not in raw_data:
                score -= 30
            else:
                main = raw_data['main']
                if 'temp' not in main:
                    score -= 20
                if 'humidity' not in main:
                    score -= 10
            
            if 'weather' not in raw_data or not raw_data['weather']:
                score -= 15
            
            if 'wind' not in raw_data:
                score -= 10
            
            # Check for unrealistic values
            if 'main' in raw_data:
                main = raw_data['main']
                temp = main.get('temp', 0)
                humidity = main.get('humidity', 0)
                
                if temp < -60 or temp > 60:  # Extreme temperatures
                    score -= 20
                if humidity < 0 or humidity > 100:  # Invalid humidity
                    score -= 15
            
            return max(0, min(100, score))
            
        except Exception:
            return 50  # Default score if assessment fails
    
    def get_weather_icon_mapping(self) -> Dict[str, str]:
        """Get OpenWeatherMap icon to constitutional weather icon mapping"""
        return {
            # Day icons
            '01d': 'sunny',
            '02d': 'partly-cloudy',
            '03d': 'cloudy',
            '04d': 'cloudy',
            '09d': 'rain-moderate',
            '10d': 'rain-light',
            '11d': 'thunderstorm',
            '13d': 'snow',
            '50d': 'fog',
            
            # Night icons
            '01n': 'night',
            '02n': 'partly-cloudy',
            '03n': 'cloudy',
            '04n': 'cloudy',
            '09n': 'rain-moderate',
            '10n': 'rain-light',
            '11n': 'thunderstorm',
            '13n': 'snow',
            '50n': 'fog'
        }
    
    async def test_provider_connection(self) -> bool:
        """Test OpenWeatherMap connection"""
        try:
            # Test with Sofia, Bulgaria (MANGO RULE compliance)
            test_data = await self.get_current_weather(42.6977, 23.3219)
            
            if test_data and 'temperature' in test_data:
                logger.info("✅ OpenWeatherMap connection test successful")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ OpenWeatherMap connection test failed: {e}")
            return False
    
    def get_api_usage_info(self) -> Dict[str, Any]:
        """Get API usage information"""
        return {
            'provider': 'openweathermap',
            'api_calls_made': self.request_count,
            'api_calls_limit': self.max_requests_per_minute,
            'rate_limit_reset': self.last_reset_time,
            'constitutional_compliance': self.constitutional_compliance_score,
            'mango_rule_verified': self.mango_rule_verified
        }