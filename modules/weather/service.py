#!/usr/bin/env python3
"""
Weather service for AVA OLO Farmer Portal
Provides weather data for Bulgarian mango cooperative farmers
"""
import os
import httpx
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import json

class WeatherService:
    """Weather service using OpenWeatherMap API"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENWEATHER_API_KEY')
        self.base_url = "http://api.openweathermap.org/data/2.5"
        self.onecall_url = "https://api.openweathermap.org/data/3.0/onecall"
        
        # No default location - must be provided by farmer or return None
        self.default_location = None
    
    def _get_weather_emoji(self, weather_code: str, is_day: bool = True) -> str:
        """Get appropriate emoji for weather condition"""
        weather_emojis = {
            '01d': '☀️',  # clear sky day
            '01n': '🌙',  # clear sky night
            '02d': '⛅',  # few clouds day
            '02n': '☁️',  # few clouds night
            '03d': '☁️',  # scattered clouds
            '03n': '☁️',
            '04d': '☁️',  # broken clouds
            '04n': '☁️',
            '09d': '🌧️',  # shower rain
            '09n': '🌧️',
            '10d': '🌦️',  # rain day
            '10n': '🌧️',  # rain night
            '11d': '⛈️',  # thunderstorm
            '11n': '⛈️',
            '13d': '🌨️',  # snow
            '13n': '🌨️',
            '50d': '🌫️',  # mist
            '50n': '🌫️'
        }
        return weather_emojis.get(weather_code, '🌤️')
    
    def _format_temperature(self, temp: float) -> str:
        """Format temperature with degree symbol"""
        return f"{int(round(temp))}°C"
    
    def _format_humidity(self, humidity: int) -> str:
        """Format humidity percentage"""
        return f"{humidity}%"
    
    def _format_wind_speed(self, speed: float) -> str:
        """Format wind speed in km/h"""
        km_h = speed * 3.6  # Convert m/s to km/h
        return f"{int(round(km_h))} km/h"
    
    async def get_current_weather(self, lat: Optional[float] = None, lon: Optional[float] = None) -> Optional[Dict]:
        """Get current weather for specified location"""
        # Hardcode API key as fallback if not in environment
        if not self.api_key:
            self.api_key = "53efe5a8c7ac5cad63b7b0419f5d3069"
            print(f"WARNING: Using hardcoded API key as OPENWEATHER_API_KEY not found in environment")
        
        # Return None if no location provided
        if lat is None or lon is None:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/weather",
                    params={
                        'lat': lat,
                        'lon': lon,
                        'appid': self.api_key,
                        'units': 'metric'  # Celsius
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Add proof of location
                    data['proof'] = {
                        'requested_lat': lat,
                        'requested_lon': lon,
                        'api_returned_lat': data.get('coord', {}).get('lat'),
                        'api_returned_lon': data.get('coord', {}).get('lon'),
                        'api_returned_city': data.get('name', 'Unknown'),
                        'api_returned_country': data.get('sys', {}).get('country'),
                        'api_call_time': datetime.now().isoformat(),
                        'api_key_used': self.api_key[:8] + "..." if self.api_key else "NO KEY"
                    }
                    return self._format_current_weather(data)
                else:
                    print(f"Weather API error: {response.status_code}, Response: {response.text}")
                    # Return error with coordinates for debugging
                    return {
                        'location': f'API Error ({lat:.2f}, {lon:.2f})',
                        'temperature': 'ERR',
                        'humidity': 'ERR%',
                        'description': f'API returned {response.status_code}',
                        'icon': '❌',
                        'wind_speed': '0 km/h',
                        'rainfall_24h': 0,
                        'error': True,
                        'error_details': response.text[:200]
                    }
                    
        except Exception as e:
            print(f"Weather service error: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            # Return error instead of mock data so we can see what's wrong
            return {
                'location': f'Exception ({lat:.2f}, {lon:.2f})',
                'temperature': 'ERR',
                'humidity': 'ERR%',
                'description': str(e)[:50],
                'icon': '❌',
                'wind_speed': '0 km/h',
                'rainfall_24h': 0,
                'error': True,
                'error_type': type(e).__name__
            }
    
    async def get_hourly_forecast(self, lat: Optional[float] = None, lon: Optional[float] = None) -> Optional[List[Dict]]:
        """Get hourly forecast for next 24 hours"""
        # Hardcode API key as fallback if not in environment
        if not self.api_key:
            self.api_key = "53efe5a8c7ac5cad63b7b0419f5d3069"
        
        # Return None if no location provided
        if lat is None or lon is None:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/forecast",
                    params={
                        'lat': lat,
                        'lon': lon,
                        'appid': self.api_key,
                        'units': 'metric',
                        'cnt': 40  # Get max allowed (5 days of 3-hour intervals)
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return self._format_hourly_data_interpolated(data)
                else:
                    print(f"Hourly forecast API error: {response.status_code}")
                    return self._get_mock_hourly_data_24h()
                    
        except Exception as e:
            print(f"Hourly forecast service error: {e}")
            return self._get_mock_hourly_data_24h()
    
    def _format_hourly_data_interpolated(self, data: Dict) -> List[Dict]:
        """Format and interpolate hourly forecast data to get 24 individual hours"""
        hourly_data = []
        current_time = datetime.now()
        
        # Get 3-hour forecast data
        forecast_list = data.get('list', [])
        
        if not forecast_list:
            return self._get_mock_hourly_data_24h()
        
        # Create 24 hourly entries by interpolating between 3-hour forecasts
        for hour_offset in range(24):
            target_time = current_time + timedelta(hours=hour_offset)
            target_timestamp = target_time.timestamp()
            
            # Find surrounding 3-hour forecasts
            prev_forecast = None
            next_forecast = None
            
            for i, item in enumerate(forecast_list):
                item_timestamp = item['dt']
                if item_timestamp <= target_timestamp:
                    prev_forecast = item
                if item_timestamp >= target_timestamp and next_forecast is None:
                    next_forecast = item
                    break
            
            # If we have both, interpolate; otherwise use the closest one
            if prev_forecast and next_forecast and prev_forecast != next_forecast:
                # Linear interpolation
                prev_time = prev_forecast['dt']
                next_time = next_forecast['dt']
                weight = (target_timestamp - prev_time) / (next_time - prev_time) if next_time != prev_time else 0
                
                # Interpolate temperature
                temp = prev_forecast['main']['temp'] * (1 - weight) + next_forecast['main']['temp'] * weight
                
                # Use the closer forecast for other values
                forecast = prev_forecast if weight < 0.5 else next_forecast
            else:
                # Use the closest available forecast
                forecast = next_forecast if next_forecast else prev_forecast if prev_forecast else forecast_list[0]
                temp = forecast['main']['temp']
            
            weather = forecast['weather'][0]
            wind = forecast.get('wind', {})
            
            # Get rainfall
            rain_3h = forecast.get('rain', {}).get('3h', 0)
            snow_3h = forecast.get('snow', {}).get('3h', 0)
            # Divide by 3 to get approximate hourly rainfall
            hourly_rain = (rain_3h + snow_3h) / 3
            
            hourly_data.append({
                'time': target_time.strftime('%H:%M'),
                'hour': target_time.hour,
                'temp': int(round(temp)),
                'icon': self._get_weather_emoji(weather['icon']),
                'description': weather['description'].title(),
                'wind': {
                    'speed': int(round(wind.get('speed', 0) * 3.6)),  # Convert to km/h
                    'direction': self._get_wind_direction(wind.get('deg', 0))
                },
                'rainfall_mm': round(hourly_rain, 1),
                'humidity': forecast['main']['humidity']
            })
        
        return hourly_data
    
    def _format_hourly_data(self, data: Dict) -> List[Dict]:
        """Format hourly forecast data"""
        hourly_data = []
        
        for item in data['list']:
            dt = datetime.fromtimestamp(item['dt'])
            weather = item['weather'][0]
            main = item['main']
            wind = item.get('wind', {})
            
            # Get rainfall in mm (not percentage)
            rain_3h = item.get('rain', {}).get('3h', 0)  # mm in last 3 hours
            snow_3h = item.get('snow', {}).get('3h', 0)  # mm in last 3 hours
            total_precip = rain_3h + snow_3h
            
            hourly_data.append({
                'time': dt.strftime('%H:%M'),
                'hour': dt.hour,
                'temp': int(round(main['temp'])),
                'icon': self._get_weather_emoji(weather['icon']),
                'description': weather['description'].title(),
                'wind': {
                    'speed': int(round(wind.get('speed', 0) * 3.6)),  # Convert to km/h
                    'direction': self._get_wind_direction(wind.get('deg', 0))
                },
                'rainfall_mm': round(total_precip, 1),  # Rainfall in mm
                'humidity': main['humidity']
            })
        
        return hourly_data
    
    def _get_wind_direction(self, degrees: int) -> str:
        """Convert wind degrees to cardinal direction"""
        directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
        index = int((degrees + 22.5) / 45) % 8
        return directions[index]
    
    def _get_mock_hourly_data(self) -> List[Dict]:
        """Mock hourly data for testing (old 3-hour intervals)"""
        hourly_data = []
        current_hour = datetime.now().hour
        
        for i in range(8):  # 8 3-hour intervals = 24 hours
            hour = (current_hour + i * 3) % 24
            temp = 20 + (5 * (1 if hour < 12 else -1))  # Temperature curve
            
            hourly_data.append({
                'time': f"{hour:02d}:00",
                'hour': hour,
                'temp': temp + i,
                'icon': '☀️' if 6 <= hour <= 18 else '🌙',
                'description': 'Clear' if i % 3 == 0 else 'Partly Cloudy',
                'wind': {
                    'speed': 10 + i * 2,
                    'direction': ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'][i]
                },
                'rainfall_mm': 0 if i < 5 else 2.5,
                'humidity': 60 + i * 2
            })
        
        return hourly_data
    
    def _get_mock_hourly_data_24h(self) -> List[Dict]:
        """Mock hourly data for testing - 24 individual hours"""
        hourly_data = []
        current_hour = datetime.now().hour
        
        for i in range(24):  # 24 individual hours
            hour = (current_hour + i) % 24
            # Temperature curve: cooler at night, warmer during day
            if 0 <= hour < 6:
                temp = 15 + hour  # 15-20°C early morning
            elif 6 <= hour < 12:
                temp = 20 + (hour - 6)  # 20-26°C morning
            elif 12 <= hour < 18:
                temp = 26 - (hour - 12) // 2  # 26-23°C afternoon
            else:
                temp = 23 - (hour - 18)  # 23-17°C evening
            
            hourly_data.append({
                'time': f"{hour:02d}:00",
                'hour': hour,
                'temp': temp,
                'icon': '☀️' if 6 <= hour <= 18 else '🌙',
                'description': 'Clear' if i % 4 == 0 else 'Partly Cloudy',
                'wind': {
                    'speed': 8 + (i % 5) * 2,
                    'direction': ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'][i % 8]
                },
                'rainfall_mm': 0 if i < 18 else round(i / 10, 1),  # Some evening rain
                'humidity': 55 + (i % 3) * 5
            })
        
        return hourly_data
    
    async def get_weather_forecast(self, lat: Optional[float] = None, lon: Optional[float] = None, days: int = 5) -> Optional[Dict]:
        """Get weather forecast for specified location"""
        # Hardcode API key as fallback if not in environment
        if not self.api_key:
            self.api_key = "53efe5a8c7ac5cad63b7b0419f5d3069"
        
        # Return None if no location provided
        if lat is None or lon is None:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/forecast",
                    params={
                        'lat': lat,
                        'lon': lon,
                        'appid': self.api_key,
                        'units': 'metric',
                        'cnt': days * 8  # 8 forecasts per day (3-hour intervals)
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return self._format_forecast_data(data)
                else:
                    print(f"Weather forecast API error: {response.status_code}")
                    return self._get_mock_forecast_data()
                    
        except Exception as e:
            print(f"Weather forecast service error: {e}")
            return self._get_mock_forecast_data()
    
    def _format_current_weather(self, data: Dict) -> Dict:
        """Format current weather data for display"""
        weather = data['weather'][0]
        main = data['main']
        wind = data.get('wind', {})
        
        # Get rainfall data - OpenWeather provides rain volume for last 1h and 3h
        rain_1h = data.get('rain', {}).get('1h', 0)  # mm in last hour
        rain_3h = data.get('rain', {}).get('3h', 0)  # mm in last 3 hours
        snow_1h = data.get('snow', {}).get('1h', 0)  # mm in last hour
        snow_3h = data.get('snow', {}).get('3h', 0)  # mm in last 3 hours
        
        # Use 3h data and extrapolate for 24h estimate (very rough)
        # Better would be to call history API but that costs extra
        rainfall_3h = rain_3h + snow_3h
        rainfall_24h_estimate = rainfall_3h * 8  # Rough estimate
        
        return {
            'location': data['name'],
            'temperature': self._format_temperature(main['temp']),
            'feels_like': self._format_temperature(main['feels_like']),
            'humidity': self._format_humidity(main['humidity']),
            'description': weather['description'].title(),
            'icon': self._get_weather_emoji(weather['icon']),
            'wind_speed': self._format_wind_speed(wind.get('speed', 0)),
            'pressure': f"{main['pressure']} hPa",
            'visibility': f"{data.get('visibility', 10000) // 1000} km",
            'timestamp': datetime.now().strftime('%H:%M'),
            'raw_temp': main['temp'],
            'raw_humidity': main['humidity'],
            'weather_code': weather['icon'],
            'rainfall_1h': round(rain_1h + snow_1h, 1),  # mm in last hour
            'rainfall_3h': round(rainfall_3h, 1),  # mm in last 3 hours
            'rainfall_24h': round(rainfall_24h_estimate, 1),  # Estimated mm in last 24h
            'proof': data.get('proof', {})
        }
    
    def _format_forecast_data(self, data: Dict) -> Dict:
        """Format forecast data for display"""
        daily_forecasts = []
        current_date = None
        daily_data = {}
        today = datetime.now().date()
        
        for item in data['list']:
            dt = datetime.fromtimestamp(item['dt'])
            date_key = dt.strftime('%Y-%m-%d')
            
            if current_date != date_key:
                # Save previous day if exists
                if daily_data:
                    daily_forecasts.append(daily_data)
                
                # Start new day
                current_date = date_key
                
                # Calculate day name
                days_diff = (dt.date() - today).days
                if days_diff == 0:
                    day_display = "Today"
                elif days_diff == 1:
                    day_display = "Tomorrow"
                else:
                    day_display = dt.strftime('%A')  # Full day name
                
                daily_data = {
                    'date': dt.strftime('%Y-%m-%d'),
                    'day_name': day_display,
                    'temp_min': item['main']['temp_min'],
                    'temp_max': item['main']['temp_max'],
                    'description': item['weather'][0]['description'].title(),
                    'icon': self._get_weather_emoji(item['weather'][0]['icon']),
                    'humidity': item['main']['humidity'],
                    'wind_speed': item['wind'].get('speed', 0),
                    'wind_direction': self._get_wind_direction(item['wind'].get('deg', 0)),
                    'rainfall_mm': 0  # Will accumulate
                }
            else:
                # Update min/max temps for the day
                daily_data['temp_min'] = min(daily_data['temp_min'], item['main']['temp_min'])
                daily_data['temp_max'] = max(daily_data['temp_max'], item['main']['temp_max'])
            
            # Accumulate rainfall for the day
            rain_3h = item.get('rain', {}).get('3h', 0)
            snow_3h = item.get('snow', {}).get('3h', 0)
            daily_data['rainfall_mm'] += (rain_3h + snow_3h)
        
        # Add last day
        if daily_data:
            daily_forecasts.append(daily_data)
        
        # Format the forecasts
        formatted_forecasts = []
        for forecast in daily_forecasts[:5]:  # Limit to 5 days
            formatted_forecasts.append({
                'date': forecast['date'],
                'day_name': forecast['day_name'],
                'temp_min': self._format_temperature(forecast['temp_min']),
                'temp_max': self._format_temperature(forecast['temp_max']),
                'description': forecast['description'],
                'icon': forecast['icon'],
                'humidity': self._format_humidity(forecast['humidity']),
                'wind_speed': self._format_wind_speed(forecast['wind_speed']),
                'wind_direction': forecast.get('wind_direction', ''),
                'rainfall': f"{forecast['rainfall_mm']:.1f} mm" if forecast.get('rainfall_mm', 0) > 0 else "0 mm"
            })
        
        return {
            'location': data['city']['name'],
            'forecasts': formatted_forecasts
        }
    
    def _get_mock_weather_data(self) -> Dict:
        """Mock weather data for testing/fallback"""
        return {
            'location': 'Location not set',
            'temperature': '18°C',
            'feels_like': '17°C',
            'humidity': '72%',
            'description': 'Partly Cloudy',
            'icon': '⛅',
            'wind_speed': '8 km/h',
            'pressure': '1015 hPa',
            'visibility': '10 km',
            'timestamp': datetime.now().strftime('%H:%M'),
            'raw_temp': 18.0,
            'raw_humidity': 72,
            'weather_code': '02d'
        }
    
    def _get_mock_forecast_data(self) -> Dict:
        """Mock forecast data for testing/fallback"""
        forecasts = []
        base_date = datetime.now()
        
        for i in range(5):
            date = base_date + timedelta(days=i)
            temp_base = 16 + (i * 2)  # Varying temperatures suitable for Slovenia
            
            forecasts.append({
                'date': date.strftime('%Y-%m-%d'),
                'day_name': date.strftime('%A'),
                'temp_min': f"{temp_base - 3}°C",
                'temp_max': f"{temp_base + 5}°C",
                'description': ['Sunny', 'Partly Cloudy', 'Cloudy', 'Light Rain', 'Sunny'][i],
                'icon': ['☀️', '⛅', '☁️', '🌧️', '☀️'][i],
                'humidity': f"{65 + i * 5}%",
                'wind_speed': f"{8 + i * 2} km/h",
                'wind_direction': ['N', 'NE', 'E', 'SE', 'S'][i],
                'precipitation': '0 mm' if i != 3 else '2.5 mm'
            })
        
        return {
            'location': 'Location not set',
            'forecasts': forecasts
        }
    
    async def get_weather_alerts(self, lat: Optional[float] = None, lon: Optional[float] = None) -> List[Dict]:
        """Get weather alerts for farming (frost, heat, storm warnings)"""
        current_weather = await self.get_current_weather(lat, lon)
        
        alerts = []
        
        if current_weather:
            temp = current_weather['raw_temp']
            humidity = current_weather['raw_humidity']
            
            # Frost warning
            if temp <= 2:
                alerts.append({
                    'type': 'frost',
                    'severity': 'high',
                    'title': '❄️ Frost Warning',
                    'message': 'Temperature is near freezing. Protect sensitive crops.',
                    'action': 'Cover plants or move to greenhouse'
                })
            
            # Heat warning for mango trees
            elif temp >= 35:
                alerts.append({
                    'type': 'heat',
                    'severity': 'medium',
                    'title': '🔥 High Temperature Alert',
                    'message': 'Very high temperatures may stress mango trees.',
                    'action': 'Ensure adequate watering and shade'
                })
            
            # Low humidity warning
            if humidity < 40:
                alerts.append({
                    'type': 'humidity',
                    'severity': 'low',
                    'title': '💧 Low Humidity Alert',
                    'message': 'Low humidity detected. Plants may need extra watering.',
                    'action': 'Monitor soil moisture and water as needed'
                })
            
            # High humidity warning (fungal risk)
            elif humidity > 85:
                alerts.append({
                    'type': 'humidity',
                    'severity': 'medium',
                    'title': '🌫️ High Humidity Warning',
                    'message': 'High humidity increases risk of fungal diseases.',
                    'action': 'Improve ventilation and monitor for disease signs'
                })
        
        return alerts

# Global weather service instance
weather_service = WeatherService()