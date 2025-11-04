"""
Route Monitoring Service
Handles multi-location route analysis and monitoring
"""

from typing import List, Dict, Tuple
from datetime import datetime
import math
from weather_service import WeatherService
from black_ice_predictor import BlackIcePredictor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RouteMonitor:
    """Monitor entire routes for black ice conditions"""
    
    def __init__(self, weather_service: WeatherService, predictor: BlackIcePredictor):
        self.weather_service = weather_service
        self.predictor = predictor
    
    def analyze_route(self, waypoints: List[Dict]) -> Dict:
        """
        Analyze a complete route with multiple waypoints
        
        Args:
            waypoints: List of {lat, lon, name} dictionaries
            
        Returns:
            Complete route analysis with segment risks
        """
        if len(waypoints) < 2:
            raise ValueError("Route must have at least 2 waypoints")
        
        segments = []
        total_distance = 0
        max_risk = 0
        danger_zones = []
        
        # Analyze each segment
        for i in range(len(waypoints) - 1):
            start = waypoints[i]
            end = waypoints[i + 1]
            
            # Get midpoint for weather check
            mid_lat = (start['lat'] + end['lat']) / 2
            mid_lon = (start['lon'] + end['lon']) / 2
            
            # Calculate segment distance
            distance = self._calculate_distance(
                start['lat'], start['lon'],
                end['lat'], end['lon']
            )
            total_distance += distance
            
            # Get weather and prediction for segment
            try:
                weather = self.weather_service.get_current_weather(mid_lat, mid_lon)
                prediction = self.predictor.predict(
                    temperature=weather['temperature'],
                    humidity=weather['humidity'],
                    dew_point=weather['dew_point'],
                    wind_speed=weather['wind_speed'],
                    precipitation=weather.get('precipitation', 0)
                )
                
                segment_data = {
                    'segment_id': i,
                    'start': start,
                    'end': end,
                    'midpoint': {'lat': mid_lat, 'lon': mid_lon},
                    'distance_km': round(distance, 2),
                    'weather': weather,
                    'prediction': prediction,
                    'risk_level': prediction['risk_level'],
                    'probability': prediction['probability']
                }
                
                segments.append(segment_data)
                
                # Track maximum risk
                if prediction['probability'] > max_risk:
                    max_risk = prediction['probability']
                
                # Identify danger zones (high/extreme risk)
                if prediction['risk_level'] in ['high', 'extreme']:
                    danger_zones.append({
                        'segment_id': i,
                        'location': start.get('name', f"Segment {i+1}"),
                        'coordinates': {'lat': mid_lat, 'lon': mid_lon},
                        'risk_level': prediction['risk_level'],
                        'probability': prediction['probability']
                    })
                
            except Exception as e:
                logger.error(f"Error analyzing segment {i}: {e}")
                segments.append({
                    'segment_id': i,
                    'start': start,
                    'end': end,
                    'error': str(e)
                })
        
        # Calculate overall route safety score (0-100, higher is safer)
        safety_score = max(0, 100 - max_risk)
        
        # Generate route-level recommendations
        recommendations = self._generate_route_recommendations(
            segments, danger_zones, safety_score
        )
        
        return {
            'route_summary': {
                'total_waypoints': len(waypoints),
                'total_segments': len(segments),
                'total_distance_km': round(total_distance, 2),
                'max_risk_probability': round(max_risk, 1),
                'safety_score': round(safety_score, 1),
                'danger_zone_count': len(danger_zones)
            },
            'segments': segments,
            'danger_zones': danger_zones,
            'recommendations': recommendations,
            'analyzed_at': datetime.now().isoformat()
        }
    
    def monitor_locations(self, locations: List[Dict]) -> Dict:
        """
        Monitor multiple individual locations simultaneously
        
        Args:
            locations: List of {lat, lon, name} dictionaries
            
        Returns:
            Status for each location
        """
        results = []
        high_risk_count = 0
        
        for loc in locations:
            try:
                weather = self.weather_service.get_current_weather(
                    loc['lat'], loc['lon']
                )
                prediction = self.predictor.predict(
                    temperature=weather['temperature'],
                    humidity=weather['humidity'],
                    dew_point=weather['dew_point'],
                    wind_speed=weather['wind_speed'],
                    precipitation=weather.get('precipitation', 0)
                )
                
                if prediction['risk_level'] in ['high', 'extreme']:
                    high_risk_count += 1
                
                results.append({
                    'name': loc.get('name', 'Unknown'),
                    'coordinates': {'lat': loc['lat'], 'lon': loc['lon']},
                    'weather': weather,
                    'prediction': prediction,
                    'status': 'danger' if prediction['risk_level'] in ['high', 'extreme'] else 'safe'
                })
                
            except Exception as e:
                logger.error(f"Error monitoring location {loc.get('name')}: {e}")
                results.append({
                    'name': loc.get('name', 'Unknown'),
                    'coordinates': {'lat': loc['lat'], 'lon': loc['lon']},
                    'error': str(e),
                    'status': 'error'
                })
        
        return {
            'total_locations': len(locations),
            'high_risk_locations': high_risk_count,
            'locations': results,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_route_corridor(self, start: Dict, end: Dict, samples: int = 10) -> List[Dict]:
        """
        Get weather conditions along a route corridor
        
        Args:
            start: Starting point {lat, lon}
            end: Ending point {lat, lon}
            samples: Number of sample points along route
            
        Returns:
            List of weather/risk data at sample points
        """
        corridor = []
        
        for i in range(samples):
            # Interpolate position along route
            ratio = i / (samples - 1) if samples > 1 else 0
            lat = start['lat'] + (end['lat'] - start['lat']) * ratio
            lon = start['lon'] + (end['lon'] - start['lon']) * ratio
            
            try:
                weather = self.weather_service.get_current_weather(lat, lon)
                prediction = self.predictor.predict(
                    temperature=weather['temperature'],
                    humidity=weather['humidity'],
                    dew_point=weather['dew_point'],
                    wind_speed=weather['wind_speed'],
                    precipitation=weather.get('precipitation', 0)
                )
                
                corridor.append({
                    'position': i,
                    'coordinates': {'lat': lat, 'lon': lon},
                    'distance_ratio': ratio,
                    'temperature': weather['temperature'],
                    'risk_level': prediction['risk_level'],
                    'probability': prediction['probability']
                })
                
            except Exception as e:
                logger.error(f"Error sampling corridor at position {i}: {e}")
        
        return corridor
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula (km)"""
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _generate_route_recommendations(
        self, 
        segments: List[Dict], 
        danger_zones: List[Dict],
        safety_score: float
    ) -> List[str]:
        """Generate recommendations for entire route"""
        recommendations = []
        
        if safety_score >= 80:
            recommendations.append("✅ Route conditions are generally safe")
            recommendations.append("Maintain normal driving precautions")
        elif safety_score >= 60:
            recommendations.append("⚠️ Route has some risky segments")
            recommendations.append("Exercise increased caution throughout journey")
        elif safety_score >= 40:
            recommendations.append("🟠 Route has significant black ice risk")
            recommendations.append("Consider delaying travel if possible")
            recommendations.append("Reduce speed by 30-50% on entire route")
        else:
            recommendations.append("🔴 DANGER: Route has extreme black ice risk")
            recommendations.append("STRONGLY recommend avoiding this route")
            recommendations.append("If travel unavoidable, allow 2x normal time")
        
        # Specific danger zone warnings
        if danger_zones:
            recommendations.append(f"\n⚠️ {len(danger_zones)} HIGH-RISK ZONE(S) IDENTIFIED:")
            for zone in danger_zones[:3]:  # Show top 3
                recommendations.append(
                    f"  • {zone['location']}: {zone['risk_level'].upper()} "
                    f"({zone['probability']:.0f}% probability)"
                )
        
        # Add time-based recommendations
        now = datetime.now()
        if 22 <= now.hour or now.hour <= 6:
            recommendations.append("\n🌙 Night/early morning: Radiational cooling increases risk")
        
        return recommendations
