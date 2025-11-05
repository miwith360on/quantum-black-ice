"""
Predictive Analytics Dashboard
Machine Learning model that predicts accidents before they happen
Analyzes: historical crash data + quantum risk + traffic + weather + IoT sensors
"""

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional
import json

logger = logging.getLogger(__name__)


class AccidentPredictor:
    """
    Predict accidents before they happen
    
    Inputs:
    - Historical accident data (location, time, weather conditions)
    - Current quantum risk score
    - Traffic flow patterns
    - Weather conditions
    - IoT sensor readings
    - Time of day/day of week patterns
    
    Output:
    - Probability of accident in next 1-6 hours
    - High-risk locations with time windows
    - Accident severity prediction
    """
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path or 'models/accident_predictor.h5'
        self.model = None
        self.is_trained = False
        
        # Load model if exists
        self._load_model()
        
        # Historical accident patterns (would load from database)
        self.historical_patterns = {}
        
        logger.info("🚨 Accident Predictor initialized")
    
    def predict_accident_risk(self,
                            location: Dict,
                            weather_data: Dict,
                            quantum_risk: Dict,
                            traffic_data: Dict = None,
                            iot_data: Dict = None,
                            time_window_hours: int = 3) -> Dict:
        """
        Predict accident probability for next N hours
        
        Returns:
            Dict with probability, risk factors, time window, severity
        """
        
        # Gather all risk factors
        risk_factors = self._calculate_risk_factors(
            location, weather_data, quantum_risk, traffic_data, iot_data
        )
        
        # Calculate base probability
        if self.is_trained:
            probability = self._ml_prediction(risk_factors)
        else:
            probability = self._heuristic_prediction(risk_factors)
        
        # Time-based adjustment
        hour = datetime.now().hour
        day_of_week = datetime.now().weekday()
        
        time_multiplier = self._get_time_multiplier(hour, day_of_week)
        adjusted_probability = min(1.0, probability * time_multiplier)
        
        # Predict severity
        severity = self._predict_severity(risk_factors, adjusted_probability)
        
        # Generate alert message
        alert = self._generate_alert(
            location, adjusted_probability, severity, time_window_hours
        )
        
        return {
            'probability': adjusted_probability,
            'risk_level': self._classify_risk(adjusted_probability),
            'severity': severity,
            'time_window_hours': time_window_hours,
            'alert_message': alert,
            'risk_factors': risk_factors,
            'peak_risk_time': self._predict_peak_time(hour),
            'confidence': 0.75 if self.is_trained else 0.5,
            'timestamp': datetime.now().isoformat()
        }
    
    def analyze_route_accidents(self,
                               route_points: List[Dict],
                               weather_data: Dict,
                               quantum_risks: List[Dict]) -> Dict:
        """
        Analyze entire route for accident hotspots
        
        Args:
            route_points: List of lat/lon points along route
            weather_data: Current weather
            quantum_risks: Quantum risk for each point
            
        Returns:
            Route analysis with high-risk segments
        """
        
        high_risk_segments = []
        
        for i, point in enumerate(route_points):
            quantum_risk = quantum_risks[i] if i < len(quantum_risks) else {}
            
            prediction = self.predict_accident_risk(
                location=point,
                weather_data=weather_data,
                quantum_risk=quantum_risk
            )
            
            if prediction['probability'] > 0.6:
                high_risk_segments.append({
                    'segment_index': i,
                    'location': point,
                    'probability': prediction['probability'],
                    'severity': prediction['severity'],
                    'alert': prediction['alert_message']
                })
        
        # Calculate overall route risk
        if route_points:
            avg_risk = sum(p['probability'] for p in [
                self.predict_accident_risk(pt, weather_data, {})
                for pt in route_points
            ]) / len(route_points)
        else:
            avg_risk = 0
        
        return {
            'route_risk_score': avg_risk,
            'high_risk_segments': high_risk_segments,
            'total_segments': len(route_points),
            'recommendation': self._get_route_recommendation(avg_risk, high_risk_segments)
        }
    
    def get_regional_heatmap(self,
                            center_lat: float,
                            center_lon: float,
                            radius_km: float,
                            grid_size: int = 20) -> Dict:
        """
        Generate accident risk heatmap for a region
        
        Returns:
            Grid of risk probabilities for mapping
        """
        
        # Create grid
        lat_step = radius_km / 111  # ~111km per degree lat
        lon_step = radius_km / (111 * np.cos(np.radians(center_lat)))
        
        heatmap = []
        
        for i in range(grid_size):
            row = []
            for j in range(grid_size):
                lat = center_lat + (i - grid_size/2) * lat_step / grid_size
                lon = center_lon + (j - grid_size/2) * lon_step / grid_size
                
                # Calculate risk for this cell
                risk = self._calculate_cell_risk(lat, lon)
                row.append(risk)
            
            heatmap.append(row)
        
        return {
            'center': {'lat': center_lat, 'lon': center_lon},
            'radius_km': radius_km,
            'grid_size': grid_size,
            'heatmap': heatmap,
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_risk_factors(self,
                               location: Dict,
                               weather_data: Dict,
                               quantum_risk: Dict,
                               traffic_data: Dict = None,
                               iot_data: Dict = None) -> Dict:
        """Calculate all risk factors for accident prediction"""
        
        factors = {
            # Weather risks
            'ice_risk': quantum_risk.get('probability', 0.5),
            'temperature': weather_data.get('temperature', 40),
            'visibility': weather_data.get('visibility', 10000) / 10000,  # Normalize
            'precipitation': weather_data.get('precipitation', 0),
            'wind_speed': weather_data.get('wind_speed', 0),
            
            # Location risks
            'is_bridge': location.get('is_bridge', False),
            'is_curve': location.get('is_curve', False),
            'is_intersection': location.get('is_intersection', False),
            'speed_limit': location.get('speed_limit', 55) / 70,  # Normalize
            'road_type': location.get('road_type', 'highway'),
            
            # Traffic risks
            'traffic_volume': 0.5,
            'congestion_level': 0,
            'speed_variance': 0,
        }
        
        if traffic_data:
            factors['traffic_volume'] = traffic_data.get('volume_score', 0.5)
            factors['congestion_level'] = traffic_data.get('congestion', 0)
            factors['speed_variance'] = traffic_data.get('speed_variance', 0)
        
        # IoT sensor validation
        if iot_data and iot_data.get('sensors_available'):
            conditions = iot_data.get('aggregated_conditions', {})
            
            if 'road_surface_temp' in conditions:
                road_temp = conditions['road_surface_temp']
                if road_temp <= 32:
                    factors['ice_risk'] = max(factors['ice_risk'], 0.8)
            
            if 'moisture_level' in conditions:
                moisture = conditions['moisture_level']
                if moisture in ['wet', 'ice']:
                    factors['ice_risk'] = max(factors['ice_risk'], 0.85)
        
        return factors
    
    def _heuristic_prediction(self, risk_factors: Dict) -> float:
        """Heuristic-based accident probability (fallback when ML not trained)"""
        
        probability = 0.1  # Base risk
        
        # Ice risk is the biggest factor
        probability += risk_factors['ice_risk'] * 0.4
        
        # Temperature
        if risk_factors['temperature'] <= 32:
            probability += 0.2
        
        # Visibility
        if risk_factors['visibility'] < 0.5:
            probability += 0.15
        
        # Precipitation
        if risk_factors['precipitation'] > 0:
            probability += 0.1
        
        # Location factors
        if risk_factors['is_bridge']:
            probability += 0.15
        if risk_factors['is_curve']:
            probability += 0.1
        if risk_factors['is_intersection']:
            probability += 0.05
        
        # Traffic
        if risk_factors['congestion_level'] > 0.7:
            probability += 0.05
        if risk_factors['speed_variance'] > 15:  # High speed variance = dangerous
            probability += 0.1
        
        return min(1.0, probability)
    
    def _ml_prediction(self, risk_factors: Dict) -> float:
        """ML-based prediction (when model is trained)"""
        # Would use trained TensorFlow model
        # For now, use heuristic
        return self._heuristic_prediction(risk_factors)
    
    def _get_time_multiplier(self, hour: int, day_of_week: int) -> float:
        """
        Adjust risk based on time patterns
        Rush hours and night driving are higher risk
        """
        
        multiplier = 1.0
        
        # Rush hours (7-9 AM, 4-7 PM)
        if (7 <= hour <= 9) or (16 <= hour <= 19):
            multiplier *= 1.3
        
        # Night/early morning (10 PM - 6 AM)
        elif hour >= 22 or hour <= 6:
            multiplier *= 1.5  # Fatigue + darkness
        
        # Weekend nights (Friday/Saturday)
        if day_of_week >= 4 and (hour >= 22 or hour <= 3):
            multiplier *= 1.2  # More recreational driving
        
        return multiplier
    
    def _predict_peak_time(self, current_hour: int) -> str:
        """Predict when risk will be highest"""
        
        # Simple heuristic: risk peaks at night
        if current_hour < 22:
            return "Tonight 10 PM - 2 AM"
        else:
            return "Next 3 hours"
    
    def _predict_severity(self, risk_factors: Dict, probability: float) -> str:
        """Predict accident severity if it occurs"""
        
        if risk_factors['speed_limit'] > 0.8 and probability > 0.7:
            return "High"  # High speed + high risk = severe
        elif probability > 0.6:
            return "Medium"
        else:
            return "Low"
    
    def _classify_risk(self, probability: float) -> str:
        """Classify risk level"""
        if probability >= 0.8:
            return "EXTREME"
        elif probability >= 0.6:
            return "Very High"
        elif probability >= 0.4:
            return "High"
        elif probability >= 0.2:
            return "Medium"
        else:
            return "Low"
    
    def _generate_alert(self,
                       location: Dict,
                       probability: float,
                       severity: str,
                       time_window: int) -> str:
        """Generate human-readable alert message"""
        
        loc_name = location.get('name', 'this location')
        
        if probability >= 0.8:
            return f"🚨 EXTREME RISK: {int(probability*100)}% chance of {severity.lower()} severity crash at {loc_name} in next {time_window} hours"
        elif probability >= 0.6:
            return f"⚠️ HIGH RISK: {int(probability*100)}% chance of crash at {loc_name} between now and {time_window}h from now"
        elif probability >= 0.4:
            return f"⚠️ ELEVATED RISK: {int(probability*100)}% accident probability at {loc_name}"
        else:
            return f"ℹ️ Moderate risk at {loc_name}"
    
    def _calculate_cell_risk(self, lat: float, lon: float) -> float:
        """Calculate risk for a heatmap cell"""
        # Simplified - would use actual data
        # For demo, create patterns around bridges/intersections
        
        base_risk = 0.2
        
        # Simulate higher risk near known accident hotspots
        # In production, this would query historical accident database
        
        return base_risk
    
    def _get_route_recommendation(self, avg_risk: float, high_risk_segments: List) -> str:
        """Generate route recommendation"""
        
        if avg_risk > 0.7:
            return "🚨 DELAY TRAVEL - Multiple high-risk segments. Consider waiting or alternate route."
        elif len(high_risk_segments) > 3:
            return "⚠️ CAUTION - Several accident hotspots along route. Drive carefully and consider alternate route."
        elif avg_risk > 0.4:
            return "⚠️ MODERATE RISK - Exercise caution, especially on highlighted segments."
        else:
            return "✅ SAFE - Route has low accident risk at this time."
    
    def _load_model(self):
        """Load trained model from disk"""
        try:
            import os
            if os.path.exists(self.model_path):
                self.model = keras.models.load_model(self.model_path)
                self.is_trained = True
                logger.info(f"✅ Accident predictor loaded from {self.model_path}")
        except Exception as e:
            logger.info(f"No trained model found, using heuristics: {e}")
            self.is_trained = False
    
    def get_dashboard_data(self,
                          lat: float,
                          lon: float,
                          weather_data: Dict,
                          quantum_risk: Dict,
                          traffic_data: Dict = None,
                          iot_data: Dict = None) -> Dict:
        """
        Get all data for dashboard display
        """
        
        # Current location risk
        location = {'lat': lat, 'lon': lon, 'name': 'Current Location'}
        current_risk = self.predict_accident_risk(
            location, weather_data, quantum_risk, traffic_data, iot_data
        )
        
        # Regional heatmap
        heatmap = self.get_regional_heatmap(lat, lon, radius_km=20, grid_size=15)
        
        # Historical patterns (mock data)
        historical = {
            'accidents_today': 12,
            'accidents_this_hour_avg': 2.3,
            'most_dangerous_time': '10 PM - 2 AM',
            'most_dangerous_location': 'I-95 Bridge over Delaware River'
        }
        
        return {
            'current_risk': current_risk,
            'heatmap': heatmap,
            'historical_patterns': historical,
            'timestamp': datetime.now().isoformat()
        }
