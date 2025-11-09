"""
Road Weather Information System (RWIS) Integration
Connects to MesoWest API for real-time road surface temperature data from DOT sensors
Free API - sign up at https://synopticdata.com/mesonet/signup/ for 5,000 requests/day
"""

import requests
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class RWISService:
    """Get real road surface temperatures from DOT weather stations"""
    
    def __init__(self, api_token: Optional[str] = None):
        # MesoWest API - read from environment variable
        # Sign up for free token at: https://synopticdata.com/mesonet/signup/
        self.api_token = api_token or os.getenv('MESOWEST_API_TOKEN', 'demotoken')
        self.base_url = "https://api.synopticdata.com/v2"
        self.is_demo_token = self.api_token == 'demotoken'
        
        if self.is_demo_token:
            logger.warning("⚠️ Using MesoWest demo token - limited to 5 requests/minute. Set MESOWEST_API_TOKEN environment variable for 5,000/day free.")
        else:
            logger.info("✅ RWIS Service initialized with API token")
        
        logger.info("RWIS Service initialized (MesoWest)")
    
    def get_nearby_road_sensors(self, lat: float, lon: float, radius_miles: int = 25) -> List[Dict]:
        """
        Find nearby RWIS stations (road weather sensors)
        
        Args:
            lat: Latitude
            lon: Longitude
            radius_miles: Search radius in miles (default 25)
            
        Returns:
            List of sensor stations with road surface temps
        """
        try:
            # MesoWest latest observations endpoint
            params = {
                'token': self.api_token,
                'radius': f"{lat},{lon},{radius_miles}",
                'vars': 'road_temp,road_subsurface_tmp,road_freezing_temp',
                'recent': 60,  # Last 60 minutes
                'network': '1,153,170',  # DOT networks (RWIS stations)
                'status': 'active'
            }
            
            response = requests.get(
                f"{self.base_url}/stations/latest",
                params=params,
                timeout=30
            )
            
            # Handle 403 Forbidden (rate limit or invalid token)
            if response.status_code == 403:
                if self.is_demo_token:
                    logger.warning("⚠️ MesoWest demo token rate limit reached. Returning gracefully with no data.")
                else:
                    logger.error("❌ MesoWest API 403 - Invalid/expired token. Check MESOWEST_API_TOKEN environment variable.")
                return []
            
            if response.status_code != 200:
                logger.warning(f"MesoWest API error: {response.status_code}")
                return []
            
            data = response.json()
            
            if data.get('SUMMARY', {}).get('RESPONSE_CODE') != 1:
                logger.warning(f"MesoWest response: {data.get('SUMMARY', {}).get('RESPONSE_MESSAGE')}")
                return []
            
            stations = data.get('STATION', [])
            logger.info(f"✅ Found {len(stations)} RWIS stations within {radius_miles} miles")
            
            return self._parse_stations(stations)
            
        except Exception as e:
            logger.error(f"RWIS sensor lookup error: {e}")
            return []
    
    def _parse_stations(self, stations: List[Dict]) -> List[Dict]:
        """Parse MesoWest station data into simplified format"""
        parsed = []
        
        for station in stations:
            try:
                obs = station.get('OBSERVATIONS', {})
                
                # Get road surface temperature (various possible variable names)
                road_temp_f = None
                
                # Try different road temp variable names
                if 'road_temp_set_1' in obs:
                    road_temp_f = self._celsius_to_fahrenheit(obs['road_temp_set_1']['value'][0])
                elif 'road_surface_temp_set_1' in obs:
                    road_temp_f = self._celsius_to_fahrenheit(obs['road_surface_temp_set_1']['value'][0])
                elif 'pavement_temperature_set_1' in obs:
                    road_temp_f = self._celsius_to_fahrenheit(obs['pavement_temperature_set_1']['value'][0])
                
                if road_temp_f is None:
                    continue  # Skip stations without road temp
                
                # Get subsurface temp if available (helps predict freezing)
                subsurface_temp_f = None
                if 'road_subsurface_tmp_set_1' in obs:
                    subsurface_temp_f = self._celsius_to_fahrenheit(obs['road_subsurface_tmp_set_1']['value'][0])
                
                parsed.append({
                    'station_id': station.get('STID'),
                    'name': station.get('NAME'),
                    'lat': station.get('LATITUDE'),
                    'lon': station.get('LONGITUDE'),
                    'elevation_ft': station.get('ELEVATION'),
                    'distance_miles': station.get('DISTANCE'),
                    'road_surface_temp_f': round(road_temp_f, 1),
                    'road_subsurface_temp_f': round(subsurface_temp_f, 1) if subsurface_temp_f else None,
                    'air_temp_f': self._get_air_temp(obs),
                    'observation_time': station.get('OBSERVATIONS', {}).get('date_time', [None])[0],
                    'is_freezing': road_temp_f <= 32.0
                })
                
            except Exception as e:
                logger.debug(f"Error parsing station {station.get('STID')}: {e}")
                continue
        
        # Sort by distance (closest first)
        parsed.sort(key=lambda x: x['distance_miles'])
        
        return parsed
    
    def _celsius_to_fahrenheit(self, celsius: float) -> float:
        """Convert Celsius to Fahrenheit"""
        return (celsius * 9/5) + 32
    
    def _get_air_temp(self, obs: Dict) -> Optional[float]:
        """Extract air temperature from observations"""
        if 'air_temp_set_1' in obs:
            return self._celsius_to_fahrenheit(obs['air_temp_set_1']['value'][0])
        return None
    
    def get_road_temp_estimate(self, lat: float, lon: float) -> Dict:
        """
        Get best road temperature estimate for location
        
        Uses closest RWIS sensor if available, otherwise returns None
        Frontend can fall back to calculated estimate
        
        Returns:
            {
                'source': 'rwis_sensor' or 'none',
                'road_temp_f': float or None,
                'confidence': 'high', 'medium', 'low',
                'distance_miles': float,
                'station_name': str,
                'sensor_count': int
            }
        """
        sensors = self.get_nearby_road_sensors(lat, lon, radius_miles=25)
        
        if not sensors:
            return {
                'source': 'none',
                'road_temp_f': None,
                'confidence': 'low',
                'distance_miles': None,
                'station_name': None,
                'sensor_count': 0
            }
        
        # Use closest sensor
        closest = sensors[0]
        distance = closest['distance_miles']
        
        # Determine confidence based on distance
        if distance < 5:
            confidence = 'high'
        elif distance < 15:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        return {
            'source': 'rwis_sensor',
            'road_temp_f': closest['road_surface_temp_f'],
            'subsurface_temp_f': closest['road_subsurface_temp_f'],
            'air_temp_f': closest['air_temp_f'],
            'confidence': confidence,
            'distance_miles': round(distance, 1),
            'station_name': closest['name'],
            'station_id': closest['station_id'],
            'sensor_count': len(sensors),
            'is_freezing': closest['is_freezing'],
            'observation_time': closest['observation_time']
        }
    
    def get_regional_freeze_map(self, lat: float, lon: float) -> Dict:
        """
        Get freeze status from multiple nearby sensors for regional view
        
        Returns:
            {
                'total_sensors': int,
                'frozen_sensors': int,
                'freeze_percentage': float,
                'average_road_temp': float,
                'sensors': List[Dict]
            }
        """
        sensors = self.get_nearby_road_sensors(lat, lon, radius_miles=50)
        
        if not sensors:
            return {
                'total_sensors': 0,
                'frozen_sensors': 0,
                'freeze_percentage': 0.0,
                'average_road_temp': None,
                'sensors': []
            }
        
        frozen_count = sum(1 for s in sensors if s['is_freezing'])
        avg_temp = sum(s['road_surface_temp_f'] for s in sensors) / len(sensors)
        
        return {
            'total_sensors': len(sensors),
            'frozen_sensors': frozen_count,
            'freeze_percentage': round((frozen_count / len(sensors)) * 100, 1),
            'average_road_temp': round(avg_temp, 1),
            'sensors': sensors[:10]  # Return top 10 closest
        }
