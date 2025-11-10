"""
Traffic Monitor - Google Maps Traffic Integration
Real-time traffic flow, incidents, and congestion analysis
"""

import requests
import logging
import ssl
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

logger = logging.getLogger(__name__)


class SSLAdapter(HTTPAdapter):
    """Custom adapter to force TLS 1.2+"""
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)


class TrafficMonitor:
    """Monitors real-time traffic conditions using Google Maps APIs"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api"
        self.cache = {}
        self.cache_duration = 300  # Cache for 5 minutes
        
        # Create session with TLS 1.2+ and User-Agent
        self.session = requests.Session()
        self.session.mount('https://', SSLAdapter())
        self.session.headers.update({
            'User-Agent': 'Quantum-Black-Ice-Detection/3.0 (Weather Safety Application)',
            'Accept': 'application/json'
        })
        
    def get_traffic_conditions(self, lat: float, lon: float, radius: int = 5000) -> Dict:
        """
        Get real-time traffic conditions around location
        
        Args:
            lat: Latitude
            lon: Longitude
            radius: Search radius in meters
            
        Returns:
            Traffic flow, congestion, and incident data
        """
        if not self.api_key:
            logger.warning("⚠️ Google Maps API key not configured - traffic features disabled")
            return self._empty_traffic_result()
        
        cache_key = f"{lat:.4f},{lon:.4f}"
        
        # Check cache
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if (datetime.now().timestamp() - cached_time) < self.cache_duration:
                logger.info(f"🔄 Using cached traffic data")
                return cached_data
        
        logger.info(f"🚦 Fetching live traffic for {lat:.4f}, {lon:.4f}")
        
        try:
            # Get nearby roads with traffic data
            traffic_data = self._get_traffic_flow(lat, lon, radius)
            
            # Get incidents (accidents, closures)
            incidents = self._get_traffic_incidents(lat, lon, radius)
            
            result = {
                'traffic_flow': traffic_data,
                'incidents': incidents,
                'congestion_level': self._calculate_congestion(traffic_data),
                'ice_correlation': self._correlate_with_ice(traffic_data, incidents),
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache results
            self.cache[cache_key] = (datetime.now().timestamp(), result)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Traffic monitoring error: {e}")
            return self._empty_traffic_result()
    
    def _get_traffic_flow(self, lat: float, lon: float, radius: int) -> Dict:
        """Get traffic speed and flow data"""
        
        # Note: This uses Google Roads API + Directions API for traffic
        # In production, you'd query actual traffic tiles or use a traffic-specific API
        
        try:
            # Example: Get traffic on nearby major roads
            # Using Directions API with traffic model
            
            # Define a short route around the point to sample traffic
            destination_lat = lat + 0.01  # ~1km north
            destination_lon = lon
            
            url = f"{self.base_url}/directions/json"
            params = {
                'origin': f"{lat},{lon}",
                'destination': f"{destination_lat},{destination_lon}",
                'departure_time': 'now',
                'traffic_model': 'best_guess',
                'key': self.api_key
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'OK':
                route = data['routes'][0]['legs'][0]
                
                # Extract traffic info
                duration = route.get('duration', {}).get('value', 0)  # Seconds
                duration_in_traffic = route.get('duration_in_traffic', {}).get('value', 0)
                distance = route.get('distance', {}).get('value', 0)  # Meters
                
                # Calculate traffic delay
                delay = duration_in_traffic - duration
                delay_percent = (delay / duration * 100) if duration > 0 else 0
                
                # Estimate speed
                speed_kmh = (distance / duration_in_traffic * 3.6) if duration_in_traffic > 0 else 0
                
                return {
                    'average_speed_kmh': round(speed_kmh, 1),
                    'average_speed_mph': round(speed_kmh * 0.621371, 1),
                    'delay_seconds': delay,
                    'delay_percent': round(delay_percent, 1),
                    'flow_status': self._get_flow_status(delay_percent),
                    'sample_distance_m': distance
                }
            else:
                logger.warning(f"⚠️ Directions API returned: {data['status']}")
                return self._empty_flow_data()
                
        except Exception as e:
            logger.error(f"❌ Traffic flow error: {e}")
            return self._empty_flow_data()
    
    def _get_traffic_incidents(self, lat: float, lon: float, radius: int) -> List[Dict]:
        """
        Get traffic incidents (accidents, closures, hazards)
        Note: Google Maps doesn't have a public incidents API
        Would need to use Places API to search for reported issues
        """
        
        # For a production app, you'd integrate with:
        # - Waze API (if available)
        # - HERE Traffic API (has incidents)
        # - TomTom Traffic Incidents API
        
        # Placeholder implementation using Places API to search for "accident" reports
        # In reality, this isn't reliable - just showing the structure
        
        incidents = []
        
        try:
            # Could use Places API with text search
            # but it won't give real-time traffic incidents reliably
            
            # For now, return empty - would need proper incident API
            pass
            
        except Exception as e:
            logger.error(f"❌ Incident fetch error: {e}")
        
        return incidents
    
    def _get_flow_status(self, delay_percent: float) -> str:
        """Convert delay percentage to flow status"""
        if delay_percent < 10:
            return "FREE_FLOW"
        elif delay_percent < 30:
            return "LIGHT"
        elif delay_percent < 60:
            return "MODERATE"
        elif delay_percent < 100:
            return "HEAVY"
        else:
            return "SEVERE"
    
    def _calculate_congestion(self, traffic_data: Dict) -> str:
        """Calculate overall congestion level"""
        flow = traffic_data.get('flow_status', 'UNKNOWN')
        
        if flow == 'FREE_FLOW':
            return "No congestion"
        elif flow == 'LIGHT':
            return "Light traffic"
        elif flow == 'MODERATE':
            return "Moderate congestion"
        elif flow == 'HEAVY':
            return "Heavy traffic"
        elif flow == 'SEVERE':
            return "Severe congestion"
        else:
            return "Unknown"
    
    def _correlate_with_ice(self, traffic_data: Dict, incidents: List[Dict]) -> Dict:
        """
        Correlate traffic patterns with potential black ice
        Sudden slowdowns + cold weather = likely ice
        """
        
        flow_status = traffic_data.get('flow_status', 'UNKNOWN')
        speed_mph = traffic_data.get('average_speed_mph', 0)
        
        ice_likelihood = "LOW"
        reasoning = []
        
        # Severe congestion on normally free-flowing roads = possible ice
        if flow_status in ['HEAVY', 'SEVERE']:
            ice_likelihood = "MEDIUM"
            reasoning.append("Unusual traffic slowdown detected")
        
        # Very slow speeds
        if speed_mph < 15 and flow_status != 'FREE_FLOW':
            ice_likelihood = "HIGH"
            reasoning.append("Extremely slow traffic - possible hazard")
        
        # Multiple incidents
        if len(incidents) > 2:
            ice_likelihood = "HIGH"
            reasoning.append(f"{len(incidents)} incidents reported nearby")
        
        return {
            'ice_likelihood': ice_likelihood,
            'reasoning': reasoning,
            'traffic_suggests_hazard': ice_likelihood in ['MEDIUM', 'HIGH']
        }
    
    def _empty_traffic_result(self) -> Dict:
        """Return empty traffic result"""
        return {
            'traffic_flow': self._empty_flow_data(),
            'incidents': [],
            'congestion_level': 'Unknown - API key not configured',
            'ice_correlation': {
                'ice_likelihood': 'UNKNOWN',
                'reasoning': ['Traffic monitoring requires Google Maps API key'],
                'traffic_suggests_hazard': False
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def _empty_flow_data(self) -> Dict:
        """Return empty flow data"""
        return {
            'average_speed_kmh': 0,
            'average_speed_mph': 0,
            'delay_seconds': 0,
            'delay_percent': 0,
            'flow_status': 'UNKNOWN',
            'sample_distance_m': 0
        }
    
    def get_traffic_tile_url(self, zoom: int = 13) -> Optional[str]:
        """
        Get URL for traffic layer tiles (for map overlay)
        
        Args:
            zoom: Map zoom level
            
        Returns:
            URL template for traffic tiles
        """
        if not self.api_key:
            return None
        
        # Google Maps traffic layer tile URL
        # Format: https://mt1.google.com/vt?lyrs=traffic&x={x}&y={y}&z={z}
        # Note: May require proper authentication in production
        
        return f"https://mt1.google.com/vt?lyrs=traffic&x={{x}}&y={{y}}&z={{z}}&key={self.api_key}"
    
    def analyze_route_traffic(self, origin: Tuple[float, float], 
                             destination: Tuple[float, float],
                             weather_risk: float) -> Dict:
        """
        Analyze traffic along a route combined with weather risk
        
        Args:
            origin: (lat, lon) tuple
            destination: (lat, lon) tuple  
            weather_risk: Current black ice risk (0-100)
            
        Returns:
            Route traffic analysis with ice warnings
        """
        if not self.api_key:
            return {
                'route_safe': True,
                'warnings': ['Traffic monitoring requires Google Maps API key'],
                'estimated_time': 0,
                'ice_risk_zones': []
            }
        
        try:
            # Get route with traffic
            url = f"{self.base_url}/directions/json"
            params = {
                'origin': f"{origin[0]},{origin[1]}",
                'destination': f"{destination[0]},{destination[1]}",
                'departure_time': 'now',
                'traffic_model': 'best_guess',
                'key': self.api_key
            }
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] != 'OK':
                return {'error': f"Directions API error: {data['status']}"}
            
            route = data['routes'][0]
            leg = route['legs'][0]
            
            duration_normal = leg.get('duration', {}).get('value', 0)
            duration_traffic = leg.get('duration_in_traffic', {}).get('value', 0)
            distance = leg.get('distance', {}).get('value', 0)
            
            # Analyze each step for high-risk areas
            ice_risk_zones = []
            for step in leg.get('steps', []):
                step_duration = step.get('duration', {}).get('value', 0)
                step_distance = step.get('distance', {}).get('value', 0)
                
                # Check for bridges/overpasses in instructions
                instructions = step.get('html_instructions', '').lower()
                if any(keyword in instructions for keyword in ['bridge', 'overpass', 'elevated']):
                    ice_risk_zones.append({
                        'location': step['end_location'],
                        'instruction': step['html_instructions'],
                        'risk': 'HIGH',
                        'reason': 'Bridge/overpass detected'
                    })
            
            warnings = []
            if weather_risk > 50 and (duration_traffic - duration_normal) > 300:
                warnings.append("⚠️ Significant traffic delays + ice risk - consider alternate route")
            
            if weather_risk > 60 and len(ice_risk_zones) > 0:
                warnings.append(f"🌉 {len(ice_risk_zones)} bridges/overpasses on route - EXTREME CAUTION")
            
            return {
                'route_safe': weather_risk < 50 or (duration_traffic - duration_normal) < 600,
                'warnings': warnings,
                'estimated_time_minutes': round(duration_traffic / 60, 1),
                'traffic_delay_minutes': round((duration_traffic - duration_normal) / 60, 1),
                'distance_km': round(distance / 1000, 1),
                'ice_risk_zones': ice_risk_zones,
                'overall_risk': 'HIGH' if weather_risk > 60 else 'MEDIUM' if weather_risk > 40 else 'LOW'
            }
            
        except Exception as e:
            logger.error(f"❌ Route traffic analysis error: {e}")
            return {'error': str(e)}
