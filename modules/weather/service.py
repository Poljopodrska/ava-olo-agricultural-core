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
        
        # Default location for Bulgarian mango farms (approximate)
        self.default_location = {
            'lat': 42.7339,  # Bulgaria latitude
            'lon': 25.4858,  # Bulgaria longitude
            'name': 'Bulgaria'
        }
    
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
        if not self.api_key:
            return self._get_mock_weather_data()
        
        # Use default location if not specified
        if lat is None or lon is None:
            lat = self.default_location['lat']
            lon = self.default_location['lon']
        
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
                    return self._format_current_weather(data)
                else:
                    print(f"Weather API error: {response.status_code}")
                    return self._get_mock_weather_data()
                    
        except Exception as e:
            print(f"Weather service error: {e}")
            return self._get_mock_weather_data()
    
    async def get_hourly_forecast(self, lat: Optional[float] = None, lon: Optional[float] = None) -> Optional[List[Dict]]:
        """Get hourly forecast for next 24 hours"""
        if not self.api_key:
            return self._get_mock_hourly_data()
        
        # Use default location if not specified
        if lat is None or lon is None:
            lat = self.default_location['lat']
            lon = self.default_location['lon']
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/forecast",
                    params={
                        'lat': lat,
                        'lon': lon,
                        'appid': self.api_key,
                        'units': 'metric',
                        'cnt': 8  # Next 24 hours (3-hour intervals)
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return self._format_hourly_data(data)
                else:
                    print(f"Hourly forecast API error: {response.status_code}")
                    return self._get_mock_hourly_data()
                    
        except Exception as e:
            print(f"Hourly forecast service error: {e}")
            return self._get_mock_hourly_data()
    
    def _format_hourly_data(self, data: Dict) -> List[Dict]:
        """Format hourly forecast data"""
        hourly_data = []
        
        for item in data['list']:
            dt = datetime.fromtimestamp(item['dt'])
            weather = item['weather'][0]
            main = item['main']
            wind = item.get('wind', {})
            
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
                'precipitation': item.get('rain', {}).get('3h', 0),
                'humidity': main['humidity']
            })
        
        return hourly_data
    
    def _get_wind_direction(self, degrees: int) -> str:
        """Convert wind degrees to cardinal direction"""
        directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
        index = int((degrees + 22.5) / 45) % 8
        return directions[index]
    
    def _get_mock_hourly_data(self) -> List[Dict]:
        """Mock hourly data for testing"""
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
                'precipitation': 0 if i < 5 else 2.5,
                'humidity': 60 + i * 2
            })
        
        return hourly_data
    
    async def get_weather_forecast(self, lat: Optional[float] = None, lon: Optional[float] = None, days: int = 5) -> Optional[Dict]:
        """Get weather forecast for specified location"""
        if not self.api_key:
            return self._get_mock_forecast_data()
        
        # Use default location if not specified
        if lat is None or lon is None:
            lat = self.default_location['lat']
            lon = self.default_location['lon']
        
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
            'weather_code': weather['icon']
        }
    
    def _format_forecast_data(self, data: Dict) -> Dict:
        """Format forecast data for display"""
        daily_forecasts = []
        current_date = None
        daily_data = {}
        
        for item in data['list']:
            dt = datetime.fromtimestamp(item['dt'])
            date_key = dt.strftime('%Y-%m-%d')
            
            if current_date != date_key:
                # Save previous day if exists
                if daily_data:
                    daily_forecasts.append(daily_data)
                
                # Start new day
                current_date = date_key
                daily_data = {
                    'date': dt.strftime('%Y-%m-%d'),
                    'day_name': dt.strftime('%A'),
                    'temp_min': item['main']['temp_min'],
                    'temp_max': item['main']['temp_max'],
                    'description': item['weather'][0]['description'].title(),
                    'icon': self._get_weather_emoji(item['weather'][0]['icon']),
                    'humidity': item['main']['humidity'],
                    'wind_speed': item['wind'].get('speed', 0),
                    'precipitation': item.get('rain', {}).get('3h', 0)
                }
            else:
                # Update min/max temps for the day
                daily_data['temp_min'] = min(daily_data['temp_min'], item['main']['temp_min'])
                daily_data['temp_max'] = max(daily_data['temp_max'], item['main']['temp_max'])
        
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
                'precipitation': f"{forecast['precipitation']:.1f} mm" if forecast['precipitation'] > 0 else "No rain"
            })
        
        return {
            'location': data['city']['name'],
            'forecasts': formatted_forecasts
        }
    
    def _get_mock_weather_data(self) -> Dict:
        """Mock weather data for testing/fallback"""
        return {
            'location': 'Sofia, Bulgaria',
            'temperature': '24°C',
            'feels_like': '26°C',
            'humidity': '65%',
            'description': 'Partly Cloudy',
            'icon': '⛅',
            'wind_speed': '12 km/h',
            'pressure': '1015 hPa',
            'visibility': '10 km',
            'timestamp': datetime.now().strftime('%H:%M'),
            'raw_temp': 24.0,
            'raw_humidity': 65,
            'weather_code': '02d'
        }
    
    def _get_mock_forecast_data(self) -> Dict:
        """Mock forecast data for testing/fallback"""
        forecasts = []
        base_date = datetime.now()
        
        for i in range(5):
            date = base_date + timedelta(days=i)
            temp_base = 22 + (i * 2)  # Varying temperatures
            
            forecasts.append({
                'date': date.strftime('%Y-%m-%d'),
                'day_name': date.strftime('%A'),
                'temp_min': f"{temp_base - 3}°C",
                'temp_max': f"{temp_base + 5}°C",
                'description': ['Sunny', 'Partly Cloudy', 'Cloudy', 'Light Rain', 'Sunny'][i],
                'icon': ['☀️', '⛅', '☁️', '🌧️', '☀️'][i],
                'humidity': f"{60 + i * 5}%",
                'wind_speed': f"{10 + i * 2} km/h",
                'precipitation': ['No rain', 'No rain', 'No rain', '2.5 mm', 'No rain'][i]
            })
        
        return {
            'location': 'Sofia, Bulgaria',
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