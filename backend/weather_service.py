"""
Weather Service Module
Handles communication with OpenWeatherMap API
"""

import requests
from typing import Dict, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WeatherService:
    """Service for fetching weather data from OpenWeatherMap API"""
    
    BASE_URL = "https://api.openweathermap.org/data/2.5"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        if not api_key:
            logger.warning("OpenWeatherMap API key not provided!")
    
    def get_current_weather(self, lat: float, lon: float) -> Dict:
        """
        Fetch current weather data for a location
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary containing weather data
        """
        try:
            url = f"{self.BASE_URL}/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Calculate dew point
            temperature_c = data['main']['temp']
            feels_like_c = data['main']['feels_like']
            humidity = data['main']['humidity']
            dew_point_c = self._calculate_dew_point(temperature_c, humidity)
            
            # Convert to Fahrenheit for consistency with rest of system
            temperature_f = (temperature_c * 9/5) + 32
            feels_like_f = (feels_like_c * 9/5) + 32
            dew_point_f = (dew_point_c * 9/5) + 32
            wind_mph = data['wind']['speed'] * 2.237  # m/s to mph
            
            return {
                'temperature': temperature_f,
                'feels_like': feels_like_f,
                'humidity': humidity,
                'pressure': data['main']['pressure'],
                'dew_point': dew_point_f,
                'wind_speed': wind_mph,
                'wind_deg': data['wind'].get('deg', 0),
                'clouds': data['clouds']['all'],
                'visibility': data.get('visibility', 10000),
                'precipitation': data.get('rain', {}).get('1h', 0) + data.get('snow', {}).get('1h', 0),
                'weather': data['weather'][0]['main'],
                'description': data['weather'][0]['description'],
                'timestamp': datetime.fromtimestamp(data['dt']).isoformat(),
                'location': data['name']
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching weather data: {e}")
            raise Exception(f"Failed to fetch weather data: {str(e)}")
    
    def get_forecast(self, lat: float, lon: float, hours: int = 48) -> list:
        """
        Fetch weather forecast for a location
        
        Args:
            lat: Latitude
            lon: Longitude
            hours: Number of hours to forecast (default 48)
            
        Returns:
            List of forecast data points
        """
        try:
            url = f"{self.BASE_URL}/forecast"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            forecast = []
            for item in data['list'][:hours // 3]:  # API returns 3-hour intervals
                temperature = item['main']['temp']
                humidity = item['main']['humidity']
                dew_point = self._calculate_dew_point(temperature, humidity)
                
                forecast.append({
                    'timestamp': datetime.fromtimestamp(item['dt']).isoformat(),
                    'temperature': temperature,
                    'humidity': humidity,
                    'dew_point': dew_point,
                    'wind_speed': item['wind']['speed'],
                    'precipitation': item.get('rain', {}).get('3h', 0) + item.get('snow', {}).get('3h', 0),
                    'weather': item['weather'][0]['main']
                })
            
            return forecast
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching forecast: {e}")
            raise Exception(f"Failed to fetch forecast: {str(e)}")
    
    @staticmethod
    def _calculate_dew_point(temperature: float, humidity: float) -> float:
        """
        Calculate dew point using Magnus formula
        
        Args:
            temperature: Temperature in Celsius
            humidity: Relative humidity (0-100)
            
        Returns:
            Dew point in Celsius
        """
        # Magnus formula constants
        a = 17.27
        b = 237.7
        
        alpha = ((a * temperature) / (b + temperature)) + (humidity / 100.0)
        dew_point = (b * alpha) / (a - alpha)
        
        return round(dew_point, 2)
