"""
NOAA Weather.gov API Service
Provides high-quality US weather data, alerts, and forecasts
"""

import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class NOAAWeatherService:
    """
    NOAA Weather.gov API integration
    Provides more accurate US weather data than OpenWeather
    """
    
    def __init__(self):
        self.base_url = "https://api.weather.gov"
        self.headers = {
            'User-Agent': '(Quantum Black Ice Detection, contact@example.com)',
            'Accept': 'application/json'
        }
        logger.info("NOAA Weather Service initialized")
    
    def get_gridpoint(self, lat, lon):
        """
        Get NOAA gridpoint for coordinates
        Required for forecast API calls
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            Dict with office and grid coordinates
        """
        try:
            url = f"{self.base_url}/points/{lat},{lon}"
            response = requests.get(url, headers=self.headers, timeout=30)  # Increased from 10 to 30
            response.raise_for_status()
            
            data = response.json()
            properties = data.get('properties', {})
            
            gridpoint = {
                'office': properties.get('gridId'),
                'gridX': properties.get('gridX'),
                'gridY': properties.get('gridY'),
                'forecast_url': properties.get('forecast'),
                'hourly_forecast_url': properties.get('forecastHourly'),
                'observation_stations_url': properties.get('observationStations')
            }
            
            logger.debug(f"Gridpoint for {lat},{lon}: {gridpoint['office']}/{gridpoint['gridX']},{gridpoint['gridY']}")
            
            return gridpoint
            
        except Exception as e:
            logger.error(f"Error getting gridpoint: {e}")
            return None
    
    def get_nearest_station(self, lat, lon):
        """
        Find nearest NOAA observation station
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            Station ID string
        """
        try:
            gridpoint = self.get_gridpoint(lat, lon)
            if not gridpoint:
                return None
            
            stations_url = gridpoint.get('observation_stations_url')
            if not stations_url:
                return None
            
            response = requests.get(stations_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            stations = data.get('features', [])
            
            if stations:
                # Get first (nearest) station
                station_url = stations[0].get('id')
                station_id = station_url.split('/')[-1]
                logger.debug(f"Nearest station: {station_id}")
                return station_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting nearest station: {e}")
            return None
    
    def get_current_observations(self, lat, lon):
        """
        Get current weather observations from nearest NOAA station
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            Dict with current weather data
        """
        try:
            station_id = self.get_nearest_station(lat, lon)
            if not station_id:
                logger.warning("No NOAA station found")
                return None
            
            url = f"{self.base_url}/stations/{station_id}/observations/latest"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            properties = data.get('properties', {})
            
            # Extract weather data
            weather = {
                'temperature': self._celsius_to_fahrenheit(properties.get('temperature', {}).get('value')),
                'dew_point': self._celsius_to_fahrenheit(properties.get('dewpoint', {}).get('value')),
                'humidity': properties.get('relativeHumidity', {}).get('value'),
                'wind_speed': self._mps_to_mph(properties.get('windSpeed', {}).get('value')),
                'wind_direction': properties.get('windDirection', {}).get('value'),
                'wind_gust': self._mps_to_mph(properties.get('windGust', {}).get('value')),
                'pressure': self._pa_to_mb(properties.get('barometricPressure', {}).get('value')),
                'visibility': properties.get('visibility', {}).get('value'),  # meters
                'clouds': self._parse_cloud_cover(properties.get('textDescription', '')),
                'weather_description': properties.get('textDescription', ''),
                'timestamp': properties.get('timestamp'),
                'station': station_id
            }
            
            logger.info(f"NOAA observations: {weather['temperature']}°F, {weather['humidity']}% humidity")
            
            return weather
            
        except Exception as e:
            logger.error(f"Error getting current observations: {e}")
            return None
    
    def get_hourly_forecast(self, lat, lon, hours=12):
        """
        Get hourly forecast from NOAA
        
        Args:
            lat: Latitude
            lon: Longitude
            hours: Number of hours to forecast
        
        Returns:
            List of hourly forecast dicts
        """
        try:
            gridpoint = self.get_gridpoint(lat, lon)
            if not gridpoint:
                return None
            
            forecast_url = gridpoint.get('hourly_forecast_url')
            if not forecast_url:
                return None
            
            response = requests.get(forecast_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            periods = data.get('properties', {}).get('periods', [])
            
            forecasts = []
            for period in periods[:hours]:
                forecast = {
                    'time': period.get('startTime'),
                    'temperature': period.get('temperature'),
                    'wind_speed': self._parse_wind_speed(period.get('windSpeed', '0 mph')),
                    'wind_direction': period.get('windDirection'),
                    'precipitation_probability': period.get('probabilityOfPrecipitation', {}).get('value', 0),
                    'dew_point': period.get('dewpoint', {}).get('value'),
                    'humidity': period.get('relativeHumidity', {}).get('value'),
                    'short_forecast': period.get('shortForecast'),
                    'detailed_forecast': period.get('detailedForecast')
                }
                forecasts.append(forecast)
            
            logger.info(f"Retrieved {len(forecasts)} hour forecast from NOAA")
            
            return forecasts
            
        except Exception as e:
            logger.error(f"Error getting hourly forecast: {e}")
            return None
    
    def get_weather_alerts(self, lat, lon):
        """
        Get active weather alerts for location
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            List of alert dicts
        """
        try:
            url = f"{self.base_url}/alerts/active?point={lat},{lon}"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            features = data.get('features', [])
            
            alerts = []
            for feature in features:
                props = feature.get('properties', {})
                alert = {
                    'event': props.get('event'),
                    'severity': props.get('severity'),
                    'certainty': props.get('certainty'),
                    'urgency': props.get('urgency'),
                    'headline': props.get('headline'),
                    'description': props.get('description'),
                    'instruction': props.get('instruction'),
                    'onset': props.get('onset'),
                    'expires': props.get('expires')
                }
                alerts.append(alert)
            
            if alerts:
                logger.warning(f"Found {len(alerts)} weather alerts for location")
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting weather alerts: {e}")
            return []
    
    # Helper methods
    
    def _celsius_to_fahrenheit(self, celsius):
        """Convert Celsius to Fahrenheit"""
        if celsius is None:
            return None
        return round((celsius * 9/5) + 32, 1)
    
    def _mps_to_mph(self, mps):
        """Convert meters per second to miles per hour"""
        if mps is None:
            return None
        return round(mps * 2.237, 1)
    
    def _pa_to_mb(self, pascals):
        """Convert pascals to millibars"""
        if pascals is None:
            return None
        return round(pascals / 100, 1)
    
    def _parse_wind_speed(self, wind_str):
        """Parse wind speed from string like '10 mph' or '5 to 10 mph'"""
        try:
            # Extract first number from string
            import re
            match = re.search(r'(\d+)', wind_str)
            if match:
                return int(match.group(1))
        except:
            pass
        return 0
    
    def _parse_cloud_cover(self, description):
        """Estimate cloud cover percentage from description"""
        description = description.lower()
        if 'clear' in description or 'sunny' in description:
            return 10
        elif 'partly cloudy' in description or 'partly sunny' in description:
            return 50
        elif 'mostly cloudy' in description or 'mostly sunny' in description:
            return 70
        elif 'cloudy' in description or 'overcast' in description:
            return 90
        else:
            return 50  # Default
