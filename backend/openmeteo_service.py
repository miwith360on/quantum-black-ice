"""
OpenMeteo Weather Service - High-Accuracy FREE Weather Data
Includes road surface temperature forecasts and detailed conditions
"""

import requests
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class OpenMeteoService:
    """
    OpenMeteo API - Professional weather data, 100% FREE
    Better accuracy than OpenWeather for many regions
    Includes road surface temperature!
    """
    
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1"
        self.cache = {}
        self.cache_duration = 600  # 10 minutes
        
    def get_current_weather(self, lat: float, lon: float) -> Dict:
        """
        Get comprehensive weather data including road surface temperature
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dict with detailed weather including road temp forecast
        """
        cache_key = f"{lat:.4f},{lon:.4f}"
        
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if (datetime.now().timestamp() - cached_time) < self.cache_duration:
                logger.info(f"🔄 Using cached OpenMeteo data")
                return cached_data
        
        logger.info(f"🌍 Fetching OpenMeteo data for {lat:.4f}, {lon:.4f}")
        
        try:
            # Request comprehensive weather data
            params = {
                'latitude': lat,
                'longitude': lon,
                'current': [
                    'temperature_2m',           # Air temp at 2m height
                    'relative_humidity_2m',     # Humidity
                    'apparent_temperature',     # Feels like
                    'precipitation',            # Current precip
                    'rain',                     # Rain amount
                    'showers',                  # Showers
                    'snowfall',                 # Snow amount
                    'weather_code',             # Weather condition code
                    'cloud_cover',              # Cloud cover %
                    'pressure_msl',             # Sea level pressure
                    'surface_pressure',         # Surface pressure
                    'wind_speed_10m',           # Wind speed
                    'wind_direction_10m',       # Wind direction
                    'wind_gusts_10m'            # Wind gusts
                ],
                'hourly': [
                    'temperature_2m',
                    'soil_temperature_0cm',     # SURFACE TEMPERATURE (road proxy!)
                    'soil_temperature_6cm',
                    'dew_point_2m',             # Dew point
                    'precipitation_probability',
                    'surface_temperature'       # Actual surface temp model
                ],
                'temperature_unit': 'fahrenheit',
                'wind_speed_unit': 'mph',
                'precipitation_unit': 'inch',
                'timezone': 'auto',
                'forecast_days': 1
            }
            
            response = requests.get(
                f"{self.base_url}/forecast",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            # Parse current conditions
            current = data.get('current', {})
            hourly = data.get('hourly', {})
            
            # Get road surface temperature (current hour)
            current_hour_index = 0  # First hour in forecast
            road_surface_temp = None
            
            if 'soil_temperature_0cm' in hourly and len(hourly['soil_temperature_0cm']) > 0:
                road_surface_temp = hourly['soil_temperature_0cm'][current_hour_index]
            elif 'surface_temperature' in hourly and len(hourly['surface_temperature']) > 0:
                road_surface_temp = hourly['surface_temperature'][current_hour_index]
            
            # Get dew point from hourly
            dew_point = None
            if 'dew_point_2m' in hourly and len(hourly['dew_point_2m']) > 0:
                dew_point = hourly['dew_point_2m'][current_hour_index]
            
            # Parse weather data
            weather_data = {
                'temperature': current.get('temperature_2m'),
                'feels_like': current.get('apparent_temperature'),
                'humidity': current.get('relative_humidity_2m'),
                'dew_point': dew_point,
                'road_surface_temp': road_surface_temp,  # KEY FOR BLACK ICE!
                'pressure': current.get('pressure_msl'),
                'wind_speed': current.get('wind_speed_10m'),
                'wind_direction': current.get('wind_direction_10m'),
                'wind_gust': current.get('wind_gusts_10m'),
                'cloud_cover': current.get('cloud_cover'),
                'precipitation': current.get('precipitation', 0),
                'rain': current.get('rain', 0),
                'snowfall': current.get('snowfall', 0),
                'weather_code': current.get('weather_code'),
                'description': self._get_weather_description(current.get('weather_code', 0)),
                'source': 'OpenMeteo',
                'timestamp': datetime.now().isoformat()
            }
            
            # Calculate black ice indicators
            weather_data['black_ice_indicators'] = self._calculate_black_ice_risk(weather_data)
            
            # Cache result
            self.cache[cache_key] = (datetime.now().timestamp(), weather_data)
            
            logger.info(f"✅ OpenMeteo: Temp={weather_data['temperature']}°F, Road={road_surface_temp}°F")
            
            return weather_data
            
        except requests.exceptions.Timeout:
            logger.error("⏱️ OpenMeteo API timeout")
            return {}
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ OpenMeteo API error: {e}")
            return {}
        except Exception as e:
            logger.error(f"❌ OpenMeteo parse error: {e}")
            return {}
    
    def _calculate_black_ice_risk(self, weather: Dict) -> Dict:
        """
        Calculate black ice risk indicators from OpenMeteo data
        Road surface temp is KEY - it's colder than air temp!
        """
        indicators = {
            'road_below_freezing': False,
            'dew_point_close': False,
            'recent_precipitation': False,
            'wind_chill_factor': False,
            'high_risk': False
        }
        
        road_temp = weather.get('road_surface_temp')
        air_temp = weather.get('temperature')
        dew_point = weather.get('dew_point')
        precip = weather.get('precipitation', 0) + weather.get('rain', 0)
        wind = weather.get('wind_speed', 0)
        
        # Check road surface temperature (most critical!)
        if road_temp is not None and road_temp <= 32:
            indicators['road_below_freezing'] = True
        
        # Check if dew point is close to temp (moisture condensing)
        if air_temp is not None and dew_point is not None:
            if abs(air_temp - dew_point) < 5:  # Within 5°F
                indicators['dew_point_close'] = True
        
        # Recent precipitation
        if precip > 0:
            indicators['recent_precipitation'] = True
        
        # Wind chill makes roads colder
        if wind > 10:
            indicators['wind_chill_factor'] = True
        
        # HIGH RISK if road is below freezing AND moisture present
        if indicators['road_below_freezing'] and (
            indicators['dew_point_close'] or indicators['recent_precipitation']
        ):
            indicators['high_risk'] = True
        
        return indicators
    
    def _get_weather_description(self, code: int) -> str:
        """
        Convert WMO weather code to description
        https://open-meteo.com/en/docs
        """
        weather_codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            56: "Light freezing drizzle",
            57: "Dense freezing drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            66: "Light freezing rain",
            67: "Heavy freezing rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail"
        }
        
        return weather_codes.get(code, f"Unknown ({code})")
    
    def get_hourly_forecast(self, lat: float, lon: float, hours: int = 12) -> Dict:
        """
        Get hourly forecast including road surface temperature
        Critical for predicting when roads will freeze
        """
        try:
            params = {
                'latitude': lat,
                'longitude': lon,
                'hourly': [
                    'temperature_2m',
                    'soil_temperature_0cm',
                    'dew_point_2m',
                    'precipitation_probability',
                    'precipitation',
                    'weather_code'
                ],
                'temperature_unit': 'fahrenheit',
                'timezone': 'auto',
                'forecast_days': 1
            }
            
            response = requests.get(
                f"{self.base_url}/forecast",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            hourly = data.get('hourly', {})
            times = hourly.get('time', [])
            
            # Build forecast array
            forecast = []
            for i in range(min(hours, len(times))):
                hour_data = {
                    'time': times[i],
                    'temperature': hourly.get('temperature_2m', [])[i] if i < len(hourly.get('temperature_2m', [])) else None,
                    'road_surface_temp': hourly.get('soil_temperature_0cm', [])[i] if i < len(hourly.get('soil_temperature_0cm', [])) else None,
                    'dew_point': hourly.get('dew_point_2m', [])[i] if i < len(hourly.get('dew_point_2m', [])) else None,
                    'precipitation_prob': hourly.get('precipitation_probability', [])[i] if i < len(hourly.get('precipitation_probability', [])) else None,
                    'precipitation': hourly.get('precipitation', [])[i] if i < len(hourly.get('precipitation', [])) else None,
                    'weather_code': hourly.get('weather_code', [])[i] if i < len(hourly.get('weather_code', [])) else None
                }
                
                # Calculate if this hour is high risk
                road_temp = hour_data['road_surface_temp']
                precip_prob = hour_data['precipitation_prob']
                
                hour_data['black_ice_risk'] = 'HIGH' if (
                    road_temp is not None and road_temp <= 32 and 
                    precip_prob is not None and precip_prob > 30
                ) else 'LOW'
                
                forecast.append(hour_data)
            
            return {
                'forecast': forecast,
                'source': 'OpenMeteo'
            }
            
        except Exception as e:
            logger.error(f"❌ Hourly forecast error: {e}")
            return {'forecast': [], 'source': 'OpenMeteo'}
