"""
Satellite & Weather Radar Integration Service
Provides real-time radar imagery and satellite data overlays
"""
import requests
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RadarService:
    """
    Integration with weather radar and satellite imagery services
    Supports NOAA, Weather.gov, and RainViewer APIs
    """
    
    def __init__(self):
        self.noaa_api_base = "https://api.weather.gov"
        self.rainviewer_api = "https://api.rainviewer.com/public/weather-maps.json"
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        
    def get_radar_layers(self, lat: float, lon: float) -> Dict:
        """
        Get available radar layers for a location
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary with radar layer information
        """
        try:
            # Get RainViewer radar data (most reliable free source)
            radar_data = self._get_rainviewer_data()
            
            # Get NOAA alerts for the area
            alerts = self._get_noaa_alerts(lat, lon)
            
            return {
                'success': True,
                'radar': radar_data,
                'alerts': alerts,
                'timestamp': datetime.now().isoformat(),
                'location': {'lat': lat, 'lon': lon}
            }
            
        except Exception as e:
            logger.error(f"Error getting radar layers: {e}")
            return {
                'success': False,
                'error': str(e),
                'radar': None,
                'alerts': []
            }
    
    def _get_rainviewer_data(self) -> Dict:
        """
        Get radar data from RainViewer API
        Provides animated precipitation radar
        """
        cache_key = 'rainviewer_data'
        
        # Check cache
        if cache_key in self.cache:
            cached_data, cache_time = self.cache[cache_key]
            if (datetime.now() - cache_time).seconds < self.cache_duration:
                return cached_data
        
        try:
            response = requests.get(self.rainviewer_api, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract radar layers
            radar_layers = []
            if 'radar' in data and 'past' in data['radar']:
                for frame in data['radar']['past']:
                    radar_layers.append({
                        'time': frame['time'],
                        'path': frame['path'],
                        'url': f"https://tilecache.rainviewer.com{frame['path']}/256/{{z}}/{{x}}/{{y}}/2/1_1.png"
                    })
            
            # Add nowcast (future predictions)
            if 'radar' in data and 'nowcast' in data['radar']:
                for frame in data['radar']['nowcast']:
                    radar_layers.append({
                        'time': frame['time'],
                        'path': frame['path'],
                        'url': f"https://tilecache.rainviewer.com{frame['path']}/256/{{z}}/{{x}}/{{y}}/2/1_1.png",
                        'forecast': True
                    })
            
            result = {
                'provider': 'RainViewer',
                'layers': radar_layers,
                'host': data.get('host', 'tilecache.rainviewer.com'),
                'generated': data.get('generated', 0)
            }
            
            # Cache the result
            self.cache[cache_key] = (result, datetime.now())
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching RainViewer data: {e}")
            return {
                'provider': 'RainViewer',
                'layers': [],
                'error': str(e)
            }
    
    def _get_noaa_alerts(self, lat: float, lon: float) -> List[Dict]:
        """
        Get NOAA weather alerts for a location
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            List of active weather alerts
        """
        cache_key = f'noaa_alerts_{lat}_{lon}'
        
        # Check cache
        if cache_key in self.cache:
            cached_data, cache_time = self.cache[cache_key]
            if (datetime.now() - cache_time).seconds < self.cache_duration:
                return cached_data
        
        try:
            # Get alerts for point
            url = f"{self.noaa_api_base}/alerts/active"
            params = {
                'point': f"{lat},{lon}",
                'status': 'actual',
                'message_type': 'alert'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            alerts = []
            if 'features' in data:
                for feature in data['features']:
                    props = feature.get('properties', {})
                    alerts.append({
                        'event': props.get('event'),
                        'severity': props.get('severity'),
                        'urgency': props.get('urgency'),
                        'headline': props.get('headline'),
                        'description': props.get('description'),
                        'instruction': props.get('instruction'),
                        'onset': props.get('onset'),
                        'expires': props.get('expires'),
                        'areas': props.get('areaDesc')
                    })
            
            # Cache the result
            self.cache[cache_key] = (alerts, datetime.now())
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error fetching NOAA alerts: {e}")
            return []
    
    def get_satellite_imagery(self, lat: float, lon: float, layer_type: str = 'visible') -> Dict:
        """
        Get satellite imagery for a location
        
        Args:
            lat: Latitude
            lon: Longitude
            layer_type: Type of imagery (visible, infrared, water_vapor)
            
        Returns:
            Dictionary with satellite layer information
        """
        try:
            # NOAA GOES satellite data
            # Note: This requires more complex integration with NOAA's data servers
            # For now, providing tile URLs that can be integrated
            
            layers = {
                'visible': {
                    'name': 'GOES Visible',
                    'description': 'Visible satellite imagery',
                    'url': 'https://mesonet.agron.iastate.edu/cache/tile.py/1.0.0/goes-visible-1km/{z}/{x}/{y}.png',
                    'attribution': 'NOAA GOES via Iowa State Mesonet'
                },
                'infrared': {
                    'name': 'GOES Infrared',
                    'description': 'Infrared satellite imagery',
                    'url': 'https://mesonet.agron.iastate.edu/cache/tile.py/1.0.0/goes-ir-4km/{z}/{x}/{y}.png',
                    'attribution': 'NOAA GOES via Iowa State Mesonet'
                },
                'water_vapor': {
                    'name': 'Water Vapor',
                    'description': 'Water vapor satellite imagery',
                    'url': 'https://mesonet.agron.iastate.edu/cache/tile.py/1.0.0/goes-wv-4km/{z}/{x}/{y}.png',
                    'attribution': 'NOAA GOES via Iowa State Mesonet'
                }
            }
            
            selected_layer = layers.get(layer_type, layers['visible'])
            
            return {
                'success': True,
                'layer': selected_layer,
                'available_layers': list(layers.keys()),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting satellite imagery: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_composite_layers(self, lat: float, lon: float) -> Dict:
        """
        Get a comprehensive set of weather overlay layers
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary with all available overlay layers
        """
        try:
            radar_data = self.get_radar_layers(lat, lon)
            satellite_data = self.get_satellite_imagery(lat, lon)
            
            # Additional weather overlays from OpenWeatherMap
            # (requires API key in production)
            owm_layers = self._get_openweather_layers()
            
            return {
                'success': True,
                'radar': radar_data.get('radar'),
                'satellite': satellite_data.get('layer'),
                'weather_overlays': owm_layers,
                'alerts': radar_data.get('alerts', []),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting composite layers: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_openweather_layers(self) -> Dict:
        """
        Get OpenWeatherMap overlay layers
        Note: Requires API key for production use
        """
        api_key = os.getenv('OPENWEATHER_API_KEY', 'demo')
        
        return {
            'precipitation': {
                'name': 'Precipitation',
                'url': f'https://tile.openweathermap.org/map/precipitation_new/{{z}}/{{x}}/{{y}}.png?appid={api_key}',
                'opacity': 0.6
            },
            'clouds': {
                'name': 'Cloud Cover',
                'url': f'https://tile.openweathermap.org/map/clouds_new/{{z}}/{{x}}/{{y}}.png?appid={api_key}',
                'opacity': 0.5
            },
            'temperature': {
                'name': 'Temperature',
                'url': f'https://tile.openweathermap.org/map/temp_new/{{z}}/{{x}}/{{y}}.png?appid={api_key}',
                'opacity': 0.7
            },
            'wind': {
                'name': 'Wind Speed',
                'url': f'https://tile.openweathermap.org/map/wind_new/{{z}}/{{x}}/{{y}}.png?appid={api_key}',
                'opacity': 0.6
            }
        }
    
    def clear_cache(self):
        """Clear the radar data cache"""
        self.cache = {}
        logger.info("Radar cache cleared")
