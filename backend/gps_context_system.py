"""
GPS Context System - Real-Time Location-Based Risk Analysis
Continuously tracks position and calculates dynamic quantum risk for nearby hazards
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import math

logger = logging.getLogger(__name__)


class GPSContextSystem:
    """
    Tracks user location and provides real-time context about nearby hazards
    Integrates with quantum predictor for dynamic risk alerts
    """
    
    def __init__(self, road_analyzer, quantum_predictor, weather_service):
        self.road_analyzer = road_analyzer
        self.quantum_predictor = quantum_predictor
        self.weather_service = weather_service
        
        self.last_location = None
        self.nearby_hazards = []
        self.active_alerts = []
        self.update_threshold = 100  # Update when moved 100m
        
    def update_location(self, lat: float, lon: float, weather_data: Optional[Dict] = None) -> Dict:
        """
        Update user location and recalculate all risks
        
        Args:
            lat: Current latitude
            lon: Current longitude
            weather_data: Optional current weather (will fetch if not provided)
            
        Returns:
            Dict with updated context, hazards, and quantum risk alerts
        """
        logger.info(f"📍 GPS Update: {lat:.6f}, {lon:.6f}")
        
        # Check if we need to update (moved significantly)
        if self.last_location:
            distance_moved = self._calculate_distance(
                self.last_location[0], self.last_location[1],
                lat, lon
            )
            
            if distance_moved < self.update_threshold:
                logger.info(f"⏭️ Skipping update - only moved {distance_moved:.0f}m")
                return {'status': 'no_update_needed', 'distance_moved': distance_moved}
        
        self.last_location = (lat, lon)
        
        # Get weather data if not provided
        if not weather_data:
            weather_data = self.weather_service.get_current_weather(lat, lon)
        
        # Get nearby road hazards
        road_hazards = self.road_analyzer.get_high_risk_roads(lat, lon, radius=2000)
        
        # Calculate quantum risk for current conditions
        quantum_result = self.quantum_predictor.predict(weather_data)
        
        # Analyze each nearby hazard with quantum risk
        hazard_alerts = self._generate_quantum_alerts(
            road_hazards,
            quantum_result,
            weather_data,
            lat,
            lon
        )
        
        # Update active alerts
        self.active_alerts = hazard_alerts
        self.nearby_hazards = road_hazards
        
        return {
            'location': {'lat': lat, 'lon': lon},
            'weather': {
                'temperature': weather_data.get('temperature'),
                'road_surface_temp': weather_data.get('road_surface_temp'),
                'conditions': weather_data.get('description')
            },
            'quantum_risk': {
                'probability': quantum_result['probability'],
                'risk_level': quantum_result['risk_level'],
                'confidence': quantum_result['confidence']
            },
            'nearby_hazards': {
                'bridges': len(road_hazards.get('bridges', [])),
                'overpasses': len(road_hazards.get('overpasses', [])),
                'total': len(road_hazards.get('bridges', [])) + len(road_hazards.get('overpasses', []))
            },
            'active_alerts': hazard_alerts,
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_quantum_alerts(self, road_hazards: Dict, quantum_result: Dict,
                                 weather_data: Dict, user_lat: float, user_lon: float) -> List[Dict]:
        """
        Generate intelligent alerts based on quantum risk + proximity
        
        Examples:
        - "High Quantum Risk on 2 Bridges — Proceed with Caution ❄️"
        - "Overpass near I-696 has 0.84 Ice Probability"
        """
        alerts = []
        
        quantum_prob = quantum_result['probability']
        risk_level = quantum_result['risk_level']
        
        # Only generate alerts if quantum risk is significant
        if quantum_prob < 0.5:
            return alerts
        
        # Check bridges - HIGHEST PRIORITY
        bridges = road_hazards.get('bridges', [])
        if bridges:
            # Find closest bridge
            closest_bridge = min(bridges, key=lambda b: b['distance'])
            distance_m = closest_bridge['distance']
            
            if distance_m < 500:  # Within 500m
                severity = 'CRITICAL' if quantum_prob > 0.7 else 'HIGH'
                
                alerts.append({
                    'type': 'BRIDGE_WARNING',
                    'severity': severity,
                    'title': f"⚠️ {severity}: Bridge Ahead",
                    'message': f"🌉 {closest_bridge['name']} ({distance_m:.0f}m ahead)\n"
                              f"🧊 Quantum Ice Probability: {quantum_prob:.2f}\n"
                              f"⚡ Risk Level: {risk_level}\n"
                              f"🌡️ Road Temp: {weather_data.get('road_surface_temp', 'N/A')}°F\n\n"
                              f"⚠️ BRIDGES FREEZE FIRST - SLOW DOWN NOW!",
                    'distance': distance_m,
                    'location': closest_bridge['center'],
                    'quantum_probability': quantum_prob,
                    'action': 'REDUCE_SPEED',
                    'timestamp': datetime.now().isoformat()
                })
            
            # If multiple high-risk bridges
            high_risk_bridges = [b for b in bridges if b['distance'] < 1000]
            if len(high_risk_bridges) > 1 and quantum_prob > 0.6:
                alerts.append({
                    'type': 'MULTIPLE_HAZARDS',
                    'severity': 'HIGH',
                    'title': f"⚠️ High Quantum Risk on {len(high_risk_bridges)} Bridges",
                    'message': f"🌉 {len(high_risk_bridges)} bridges detected within 1km\n"
                              f"🧊 Ice Probability: {quantum_prob:.2f}\n"
                              f"⚡ {risk_level} Risk Conditions\n\n"
                              f"Proceed with EXTREME caution ❄️",
                    'distance': high_risk_bridges[0]['distance'],
                    'quantum_probability': quantum_prob,
                    'action': 'EXTREME_CAUTION',
                    'timestamp': datetime.now().isoformat()
                })
        
        # Check overpasses
        overpasses = road_hazards.get('overpasses', [])
        if overpasses and quantum_prob > 0.6:
            closest = min(overpasses, key=lambda o: o['distance'])
            distance_m = closest['distance']
            
            if distance_m < 300:
                alerts.append({
                    'type': 'OVERPASS_WARNING',
                    'severity': 'HIGH',
                    'title': "🛣️ Elevated Road Ahead",
                    'message': f"Overpass: {closest['name']} ({distance_m:.0f}m)\n"
                              f"🧊 Quantum Probability: {quantum_prob:.2f}\n"
                              f"Elevated roads freeze before ground level",
                    'distance': distance_m,
                    'location': closest['center'],
                    'quantum_probability': quantum_prob,
                    'action': 'CAUTION',
                    'timestamp': datetime.now().isoformat()
                })
        
        # Check for dangerous curves in icy conditions
        curves = road_hazards.get('dangerous_curves', [])
        if curves and quantum_prob > 0.7:
            closest = min(curves, key=lambda c: c['distance'])
            if closest['distance'] < 200:
                alerts.append({
                    'type': 'CURVE_WARNING',
                    'severity': 'HIGH',
                    'title': "🔄 Dangerous Curve + Ice Risk",
                    'message': f"Sharp curve {closest['distance']:.0f}m ahead\n"
                              f"🧊 Quantum Probability: {quantum_prob:.2f}\n"
                              f"⚠️ HIGH RISK: Curve + Ice = Accidents",
                    'distance': closest['distance'],
                    'quantum_probability': quantum_prob,
                    'action': 'SLOW_DOWN',
                    'timestamp': datetime.now().isoformat()
                })
        
        # General high quantum risk alert
        if quantum_prob > 0.8 and not alerts:
            temp = weather_data.get('temperature', 'N/A')
            road_temp = weather_data.get('road_surface_temp', temp)
            
            alerts.append({
                'type': 'EXTREME_RISK',
                'severity': 'CRITICAL',
                'title': "🚨 EXTREME Black Ice Risk",
                'message': f"⚡ Quantum Analysis: {quantum_prob:.2f} probability\n"
                          f"🌡️ Road Surface: {road_temp}°F\n"
                          f"🧊 {risk_level} Risk Level\n\n"
                          f"BLACK ICE HIGHLY LIKELY - DRIVE CAREFULLY",
                'quantum_probability': quantum_prob,
                'action': 'EXTREME_CAUTION',
                'timestamp': datetime.now().isoformat()
            })
        
        # Sort by severity and distance
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2}
        alerts.sort(key=lambda a: (severity_order.get(a['severity'], 3), a.get('distance', 9999)))
        
        return alerts
    
    def get_nearest_hazard(self, lat: float, lon: float) -> Optional[Dict]:
        """Get the single nearest high-risk hazard"""
        if not self.nearby_hazards:
            return None
        
        all_hazards = []
        
        for bridge in self.nearby_hazards.get('bridges', []):
            bridge['hazard_type'] = 'BRIDGE'
            bridge['priority'] = 1
            all_hazards.append(bridge)
        
        for overpass in self.nearby_hazards.get('overpasses', []):
            overpass['hazard_type'] = 'OVERPASS'
            overpass['priority'] = 2
            all_hazards.append(overpass)
        
        if not all_hazards:
            return None
        
        # Sort by priority then distance
        all_hazards.sort(key=lambda h: (h['priority'], h['distance']))
        
        return all_hazards[0]
    
    def _calculate_distance(self, lat1: float, lon1: float, 
                           lat2: float, lon2: float) -> float:
        """Calculate distance in meters between two points"""
        R = 6371000  # Earth radius in meters
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def get_route_preview(self, destination_lat: float, destination_lon: float) -> Dict:
        """
        Preview hazards along a route before driving
        
        Args:
            destination_lat: Destination latitude
            destination_lon: Destination longitude
            
        Returns:
            Route analysis with hazard warnings
        """
        if not self.last_location:
            return {'error': 'No current location available'}
        
        # Get hazards along route corridor
        # (In production, would get actual route from directions API)
        
        start_lat, start_lon = self.last_location
        
        # Get hazards near destination
        dest_hazards = self.road_analyzer.get_high_risk_roads(
            destination_lat, destination_lon, radius=1000
        )
        
        # Get weather at destination
        dest_weather = self.weather_service.get_current_weather(
            destination_lat, destination_lon
        )
        
        # Calculate quantum risk for destination
        dest_quantum = self.quantum_predictor.predict(dest_weather)
        
        return {
            'origin': {'lat': start_lat, 'lon': start_lon},
            'destination': {'lat': destination_lat, 'lon': destination_lon},
            'destination_weather': {
                'temperature': dest_weather.get('temperature'),
                'road_temp': dest_weather.get('road_surface_temp'),
                'conditions': dest_weather.get('description')
            },
            'destination_risk': {
                'quantum_probability': dest_quantum['probability'],
                'risk_level': dest_quantum['risk_level']
            },
            'destination_hazards': {
                'bridges': len(dest_hazards.get('bridges', [])),
                'overpasses': len(dest_hazards.get('overpasses', []))
            },
            'recommendation': self._get_route_recommendation(dest_quantum['probability']),
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_route_recommendation(self, quantum_prob: float) -> str:
        """Get driving recommendation based on risk"""
        if quantum_prob > 0.8:
            return "⚠️ EXTREME CAUTION - Consider delaying trip if possible"
        elif quantum_prob > 0.6:
            return "⚠️ HIGH RISK - Drive slowly, avoid bridges if possible"
        elif quantum_prob > 0.4:
            return "⚠️ MODERATE RISK - Be alert, especially on bridges"
        else:
            return "✅ LOW RISK - Normal driving conditions"
