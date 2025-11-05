"""
Road Risk Analyzer - OpenStreetMap Integration
Detects high-risk road features: bridges, overpasses, shaded areas, elevation changes
"""

import requests
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import math

logger = logging.getLogger(__name__)


class RoadRiskAnalyzer:
    """Analyzes road features to identify black ice risk zones"""
    
    def __init__(self):
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        self.cache = {}
        self.cache_duration = 3600  # Cache results for 1 hour
        
    def get_high_risk_roads(self, lat: float, lon: float, radius: float = 5000) -> Dict:
        """
        Find high-risk road features within radius (meters) of location
        
        Args:
            lat: Latitude
            lon: Longitude
            radius: Search radius in meters (default 5km)
            
        Returns:
            Dict containing bridges, overpasses, tunnels, and other risk factors
        """
        cache_key = f"{lat:.4f},{lon:.4f},{radius}"
        
        # Check cache
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if (datetime.now().timestamp() - cached_time) < self.cache_duration:
                logger.info(f"🔄 Using cached road data for {lat:.4f}, {lon:.4f}")
                return cached_data
        
        logger.info(f"🗺️ Fetching road risk data for {lat:.4f}, {lon:.4f} (radius: {radius}m)")
        
        try:
            # Build Overpass QL query
            query = self._build_overpass_query(lat, lon, radius)
            
            response = requests.post(
                self.overpass_url,
                data={'data': query},
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Parse results
            risk_features = self._parse_road_features(data, lat, lon)
            
            # Cache results
            self.cache[cache_key] = (datetime.now().timestamp(), risk_features)
            
            logger.info(f"✅ Found {len(risk_features['bridges'])} bridges, "
                       f"{len(risk_features['overpasses'])} overpasses, "
                       f"{len(risk_features['shaded_roads'])} shaded roads")
            
            return risk_features
            
        except requests.exceptions.Timeout:
            logger.error("⏱️ Overpass API timeout")
            return self._empty_result()
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Overpass API error: {e}")
            return self._empty_result()
        except Exception as e:
            logger.error(f"❌ Road analysis error: {e}")
            return self._empty_result()
    
    def _build_overpass_query(self, lat: float, lon: float, radius: float) -> str:
        """Build Overpass QL query for road features"""
        
        # Bounding box around point
        bbox_radius = radius / 111320  # Convert meters to degrees (approximate)
        south = lat - bbox_radius
        north = lat + bbox_radius
        west = lon - bbox_radius
        east = lon + bbox_radius
        
        query = f"""
        [out:json][timeout:25];
        (
          // Bridges (freeze first!)
          way["bridge"="yes"]({south},{west},{north},{east});
          way["bridge"="viaduct"]({south},{west},{north},{east});
          
          // Overpasses
          way["highway"]["layer"="1"]({south},{west},{north},{east});
          way["highway"]["layer"="2"]({south},{west},{north},{east});
          
          // Tunnels (can have ice at entrances)
          way["tunnel"="yes"]({south},{west},{north},{east});
          
          // Tree-covered roads (shaded, stay cold)
          way["highway"]["surface"~".*"]["natural"="tree_row"]({south},{west},{north},{east});
          way["highway"]["tree-lined"="yes"]({south},{west},{north},{east});
          
          // North-facing slopes (less sun, colder)
          way["highway"]["embankment"="yes"]({south},{west},{north},{east});
          
          // Dangerous curves
          way["highway"]["curve"="yes"]({south},{west},{north},{east});
          
          // Road surface types (some freeze faster)
          way["highway"]["surface"="concrete"]({south},{west},{north},{east});
          way["highway"]["surface"="asphalt"]({south},{west},{north},{east});
        );
        out body;
        >;
        out skel qt;
        """
        
        return query
    
    def _parse_road_features(self, data: Dict, center_lat: float, center_lon: float) -> Dict:
        """Parse Overpass API response into risk features"""
        
        features = {
            'bridges': [],
            'overpasses': [],
            'tunnels': [],
            'shaded_roads': [],
            'dangerous_curves': [],
            'elevation_changes': [],
            'total_risk_score': 0
        }
        
        # Create node lookup
        nodes = {}
        for element in data.get('elements', []):
            if element['type'] == 'node':
                nodes[element['id']] = (element['lat'], element['lon'])
        
        # Process ways
        for element in data.get('elements', []):
            if element['type'] != 'way':
                continue
                
            tags = element.get('tags', {})
            node_ids = element.get('nodes', [])
            
            # Get way coordinates
            coords = []
            for node_id in node_ids:
                if node_id in nodes:
                    coords.append(nodes[node_id])
            
            if not coords:
                continue
            
            # Calculate center point of way
            avg_lat = sum(c[0] for c in coords) / len(coords)
            avg_lon = sum(c[1] for c in coords) / len(coords)
            distance = self._haversine_distance(center_lat, center_lon, avg_lat, avg_lon)
            
            road_name = tags.get('name', 'Unnamed Road')
            highway_type = tags.get('highway', 'unknown')
            
            feature = {
                'name': road_name,
                'type': highway_type,
                'distance': round(distance, 1),
                'coordinates': coords[:5],  # First 5 points
                'center': [avg_lat, avg_lon]
            }
            
            # Categorize features
            if tags.get('bridge') in ['yes', 'viaduct']:
                feature['risk_multiplier'] = 2.5  # Bridges are VERY high risk
                features['bridges'].append(feature)
                features['total_risk_score'] += 25
                
            if tags.get('layer', '0') in ['1', '2']:
                feature['risk_multiplier'] = 1.8  # Overpasses freeze early
                features['overpasses'].append(feature)
                features['total_risk_score'] += 18
                
            if tags.get('tunnel') == 'yes':
                feature['risk_multiplier'] = 1.5  # Tunnel entrances
                features['tunnels'].append(feature)
                features['total_risk_score'] += 15
                
            if tags.get('tree-lined') == 'yes' or 'tree_row' in tags.get('natural', ''):
                feature['risk_multiplier'] = 1.4  # Shaded = stays cold
                features['shaded_roads'].append(feature)
                features['total_risk_score'] += 10
                
            if tags.get('curve') == 'yes':
                feature['risk_multiplier'] = 1.6  # Curves + ice = accidents
                features['dangerous_curves'].append(feature)
                features['total_risk_score'] += 12
                
            if tags.get('embankment') == 'yes':
                feature['risk_multiplier'] = 1.3  # Elevation changes
                features['elevation_changes'].append(feature)
                features['total_risk_score'] += 8
        
        # Sort by distance
        for key in features:
            if isinstance(features[key], list):
                features[key] = sorted(features[key], key=lambda x: x.get('distance', 999))[:10]
        
        return features
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in meters"""
        R = 6371000  # Earth radius in meters
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _empty_result(self) -> Dict:
        """Return empty result structure"""
        return {
            'bridges': [],
            'overpasses': [],
            'tunnels': [],
            'shaded_roads': [],
            'dangerous_curves': [],
            'elevation_changes': [],
            'total_risk_score': 0
        }
    
    def calculate_route_risk(self, road_features: Dict, weather_risk: float) -> Dict:
        """
        Combine road features with weather risk for total assessment
        
        Args:
            road_features: Dict from get_high_risk_roads()
            weather_risk: Weather-based risk score (0-100)
            
        Returns:
            Combined risk assessment
        """
        road_risk = min(road_features['total_risk_score'], 100)
        
        # Weighted combination: 60% weather, 40% road features
        combined_risk = (weather_risk * 0.6) + (road_risk * 0.4)
        
        # Identify most dangerous feature
        danger_zones = []
        
        if road_features['bridges']:
            danger_zones.append({
                'type': 'BRIDGE',
                'severity': 'CRITICAL',
                'message': f"Bridge ahead: {road_features['bridges'][0]['name']} - Bridges freeze first!",
                'distance': road_features['bridges'][0]['distance']
            })
        
        if road_features['overpasses']:
            danger_zones.append({
                'type': 'OVERPASS',
                'severity': 'HIGH',
                'message': f"Overpass: {road_features['overpasses'][0]['name']} - Elevated roads freeze early",
                'distance': road_features['overpasses'][0]['distance']
            })
        
        if road_features['dangerous_curves'] and weather_risk > 50:
            danger_zones.append({
                'type': 'CURVE',
                'severity': 'HIGH',
                'message': f"Dangerous curve in icy conditions: {road_features['dangerous_curves'][0]['name']}",
                'distance': road_features['dangerous_curves'][0]['distance']
            })
        
        return {
            'combined_risk': round(combined_risk, 1),
            'road_risk': round(road_risk, 1),
            'weather_risk': round(weather_risk, 1),
            'danger_zones': sorted(danger_zones, key=lambda x: x['distance'])[:5],
            'warnings': self._generate_warnings(road_features, weather_risk)
        }
    
    def _generate_warnings(self, road_features: Dict, weather_risk: float) -> List[str]:
        """Generate driver warnings"""
        warnings = []
        
        if weather_risk > 60 and road_features['bridges']:
            warnings.append("⚠️ CRITICAL: Bridges nearby - expect ice even if roads are clear!")
        
        if weather_risk > 50 and road_features['overpasses']:
            warnings.append("🌉 Overpasses ahead - elevated roads freeze before ground-level roads")
        
        if weather_risk > 40 and road_features['shaded_roads']:
            warnings.append("🌲 Shaded roads detected - ice may remain after sun comes out")
        
        if weather_risk > 50 and road_features['dangerous_curves']:
            warnings.append("🔄 Curves ahead with ice risk - reduce speed significantly")
        
        if road_features['tunnels']:
            warnings.append("🚇 Tunnel entrances nearby - ice forms at temperature transitions")
        
        return warnings
