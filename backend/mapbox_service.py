"""
Mapbox Integration Service
Provides route optimization, hazard visualization, and safer route suggestions
"""

import requests
import logging
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class MapboxService:
    """Mapbox routing and mapping service"""
    
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.getenv('MAPBOX_API_KEY', 'no-token')
        self.base_url = "https://api.mapbox.com"
        self.has_token = self.api_token != 'no-token'
        
        if self.has_token:
            logger.info("✅ Mapbox Service initialized with API token")
        else:
            logger.warning("⚠️ Mapbox API token not configured (optional)")
    
    def get_directions(self, 
                      start_lat: float, 
                      start_lon: float,
                      end_lat: float,
                      end_lon: float,
                      mode: str = 'driving',
                      alternatives: bool = True) -> List[Dict]:
        """
        Get route directions with hazard analysis
        
        Args:
            start_lat: Starting latitude
            start_lon: Starting longitude
            end_lat: Ending latitude
            end_lon: Ending longitude
            mode: 'driving', 'walking', 'cycling'
            alternatives: Get alternative routes
            
        Returns:
            List of routes with hazard scores
        """
        if not self.has_token:
            logger.warning("Mapbox token not available, returning fallback route")
            return self._fallback_route(start_lat, start_lon, end_lat, end_lon)
        
        try:
            # Mapbox Directions API
            params = {
                'access_token': self.api_token,
                'alternatives': 'true' if alternatives else 'false',
                'steps': 'true',
                'geometries': 'geojson',
                'overview': 'full'
            }
            
            coordinates = f"{start_lon},{start_lat};{end_lon},{end_lat}"
            url = f"{self.base_url}/directions/v5/mapbox/{mode}/{coordinates}"
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                routes = []
                
                for route in data.get('routes', []):
                    route_info = {
                        'distance': route.get('distance', 0) / 1000,  # Convert to km
                        'duration': route.get('duration', 0) / 60,    # Convert to minutes
                        'geometry': route.get('geometry', {}),
                        'legs': route.get('legs', []),
                        'hazard_score': 0.5,  # Default moderate hazard
                        'recommendation': 'Standard route'
                    }
                    routes.append(route_info)
                
                logger.info(f"✅ Got {len(routes)} route(s) from Mapbox")
                return routes
            else:
                logger.warning(f"Mapbox API error: {response.status_code}")
                return self._fallback_route(start_lat, start_lon, end_lat, end_lon)
                
        except Exception as e:
            logger.error(f"Mapbox directions error: {e}")
            return self._fallback_route(start_lat, start_lon, end_lat, end_lon)
    
    def get_matrix(self, coordinates: List[Tuple[float, float]]) -> Optional[Dict]:
        """
        Get travel times/distances between multiple points (useful for fleet routing)
        
        Args:
            coordinates: List of (lon, lat) tuples
            
        Returns:
            Matrix of distances and durations
        """
        if not self.has_token or len(coordinates) < 2:
            return None
        
        try:
            coords_str = ";".join([f"{lon},{lat}" for lat, lon in coordinates])
            
            params = {
                'access_token': self.api_token,
            }
            
            url = f"{self.base_url}/directions-matrix/v1/mapbox/driving/{coords_str}"
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Matrix API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Mapbox matrix error: {e}")
            return None
    
    def add_hazard_layer(self, 
                        hazard_zones: List[Dict]) -> Dict:
        """
        Create a GeoJSON layer for hazard visualization
        
        Args:
            hazard_zones: List of hazard locations with risk data
            
        Returns:
            GeoJSON feature collection for map overlay
        """
        features = []
        
        for zone in hazard_zones:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [zone.get('lon'), zone.get('lat')]
                },
                "properties": {
                    "risk_level": zone.get('risk_level', 'moderate'),
                    "temperature": zone.get('temperature'),
                    "humidity": zone.get('humidity'),
                    "description": zone.get('description', 'Black ice hazard'),
                    "timestamp": datetime.now().isoformat()
                }
            }
            features.append(feature)
        
        return {
            "type": "FeatureCollection",
            "features": features
        }
    
    def get_isochrone(self,
                     lat: float,
                     lon: float,
                     minutes: int = 30,
                     profile: str = 'driving') -> Optional[Dict]:
        """
        Get area reachable within X minutes (useful for "safe driving zone")
        
        Args:
            lat: Center latitude
            lon: Center longitude
            minutes: Travel time in minutes
            profile: 'driving', 'walking', 'cycling'
            
        Returns:
            GeoJSON polygon of reachable area
        """
        if not self.has_token:
            return None
        
        try:
            params = {
                'access_token': self.api_token,
                'contours_minutes': str(minutes),
                'contours_colors': '00FF00'  # Green
            }
            
            url = f"{self.base_url}/isochrone/v1/mapbox/{profile}/{lon},{lat}"
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            logger.error(f"Isochrone error: {e}")
            return None
    
    def get_static_map(self,
                      center_lat: float,
                      center_lon: float,
                      zoom: int = 12,
                      width: int = 1280,
                      height: int = 720,
                      markers: Optional[List[Dict]] = None) -> Optional[str]:
        """
        Generate static map image URL
        
        Args:
            center_lat: Map center latitude
            center_lon: Map center longitude
            zoom: Zoom level (0-20)
            width: Image width
            height: Image height
            markers: List of marker dictionaries with lat, lon, label
            
        Returns:
            Static map image URL
        """
        if not self.has_token:
            return None
        
        try:
            # Build marker string
            marker_str = ""
            if markers:
                for marker in markers[:10]:  # Limit to 10 markers
                    lat = marker.get('lat')
                    lon = marker.get('lon')
                    label = marker.get('label', 'A')
                    color = marker.get('color', 'red')
                    marker_str += f"pin-{label}+{color}({lon},{lat})/"
            
            url = f"{self.base_url}/styles/v1/mapbox/streets-v12/static/{marker_str}{center_lon},{center_lat},{zoom},{width}x{height}"
            url += f"?access_token={self.api_token}"
            
            return url
            
        except Exception as e:
            logger.error(f"Static map error: {e}")
            return None
    
    def _fallback_route(self, 
                       start_lat: float,
                       start_lon: float,
                       end_lat: float,
                       end_lon: float) -> List[Dict]:
        """Fallback route when Mapbox is unavailable"""
        # Simple straight-line distance calculation
        import math
        
        lat_diff = end_lat - start_lat
        lon_diff = end_lon - start_lon
        
        # Rough distance in km (approximate)
        distance = math.sqrt(lat_diff**2 + lon_diff**2) * 111  # 1 degree ≈ 111 km
        duration = distance / 80  # Assume 80 km/h average
        
        return [{
            'distance': distance,
            'duration': duration,
            'geometry': {
                'type': 'LineString',
                'coordinates': [[start_lon, start_lat], [end_lon, end_lat]]
            },
            'hazard_score': 0.5,
            'recommendation': 'Direct route (Mapbox unavailable)',
            'source': 'fallback'
        }]
