"""
BIFI v3 - Machine Learning Enhanced Black Ice Formation Index
Self-calibrating system that learns from real user reports to improve accuracy
"""

import numpy as np
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class MLEnhancedBIFI:
    """
    BIFI with machine learning calibration
    
    Features:
    - Learns from user ground-truth reports
    - Adjusts weights based on prediction accuracy
    - Provides confidence scores
    - Explains predictions in plain language
    """
    
    def __init__(self, feedback_file: str = 'data/feedback_reports.json'):
        self.version = "3.0.0-ml"
        self.feedback_file = Path(feedback_file)
        
        # Default weights (will be tuned by ML)
        self.weights = {
            'temperature': 0.30,
            'humidity': 0.20,
            'dew_point': 0.20,
            'wind': 0.15,
            'time': 0.10,
            'precipitation': 0.05
        }
        
        # Historical accuracy tracking
        self.accuracy_history = []
        
        # Load and learn from past feedback
        self._load_calibration()
        
        logger.info(f"ML-Enhanced BIFI initialized (v{self.version})")
        logger.info(f"Trained on {len(self.accuracy_history)} reports")
    
    def calculate(self, weather_data: Dict) -> Dict:
        """
        Calculate BIFI with ML-calibrated weights and confidence scoring
        
        Args:
            weather_data: Current weather conditions
            
        Returns:
            Enhanced BIFI result with confidence and explanations
        """
        # Extract features
        temp = weather_data.get('temperature', 32)
        surface_temp = weather_data.get('road_temperature', 
                                       weather_data.get('surface_temp', temp - 3))
        humidity = weather_data.get('humidity', 70)
        dew_point = weather_data.get('dew_point', self._estimate_dew_point(temp, humidity))
        wind_speed = weather_data.get('wind_speed', 5)
        precipitation = weather_data.get('precipitation', 0)
        hour = weather_data.get('hour', datetime.now().hour)
        is_bridge = weather_data.get('is_bridge', False)
        
        # Calculate component scores (0-100 each)
        components = {
            'temperature': self._temp_component(temp, surface_temp),
            'humidity': self._humidity_component(humidity),
            'dew_point': self._dew_point_component(temp, dew_point),
            'wind': self._wind_component(wind_speed, temp),
            'time': self._time_component(hour),
            'precipitation': self._precip_component(precipitation, temp)
        }
        
        # Weighted BIFI score (using ML-calibrated weights)
        bifi_score = sum(
            components[key] * self.weights[key] 
            for key in components.keys()
        )
        
        # Bridge multiplier
        if is_bridge:
            bridge_mult = 1.3 + (0.02 * max(0, wind_speed - 10))  # Higher with wind
            bifi_score *= bridge_mult
        else:
            bridge_mult = 1.0
        
        # Surface freeze amplification
        if surface_temp < 32:
            bifi_score *= 1.25
        
        # Cap at 100
        bifi_score = min(bifi_score, 100)
        
        # Calculate confidence based on similar historical conditions
        confidence = self._calculate_confidence(weather_data)
        
        # Get risk level and color
        risk_level, risk_color = self._get_risk_level(bifi_score)
        
        # Generate user-friendly explanation
        explanation = self._generate_explanation(
            bifi_score, components, temp, surface_temp, 
            humidity, wind_speed, is_bridge, confidence
        )
        
        return {
            'bifi_score': round(bifi_score, 1),
            'risk_level': risk_level,
            'risk_color': risk_color,
            'confidence': round(confidence * 100, 0),
            'confidence_text': self._confidence_text(confidence),
            'explanation': explanation,
            'components': {k: round(v, 1) for k, v in components.items()},
            'weights': self.weights,
            'ml_calibrated': len(self.accuracy_history) > 0,
            'training_samples': len(self.accuracy_history),
            'version': self.version
        }
    
    def forecast_12h(self, hourly_weather: List[Dict]) -> List[Dict]:
        """
        Forecast BIFI for next 12 hours
        
        Args:
            hourly_weather: List of hourly weather forecasts
            
        Returns:
            List of BIFI predictions with timestamps
        """
        forecast = []
        
        for i, hour_data in enumerate(hourly_weather[:12]):
            hour_data['hour'] = (datetime.now() + timedelta(hours=i)).hour
            bifi_result = self.calculate(hour_data)
            
            forecast.append({
                'hour': i,
                'timestamp': (datetime.now() + timedelta(hours=i)).isoformat(),
                'bifi_score': bifi_result['bifi_score'],
                'risk_level': bifi_result['risk_level'],
                'confidence': bifi_result['confidence'],
                'temperature': hour_data.get('temperature', 32),
                'warning': self._should_warn(bifi_result['bifi_score'], i)
            })
        
        return forecast
    
    def learn_from_feedback(self, prediction: Dict, actual: str, weather: Dict):
        """
        Learn from user ground-truth report to improve accuracy
        
        Args:
            prediction: Original BIFI prediction
            actual: User report ('dry', 'wet', 'icy', 'snow')
            weather: Weather conditions at time of report
        """
        # Convert actual condition to expected BIFI range
        actual_bifi_range = {
            'dry': (0, 20),      # No black ice
            'wet': (30, 50),     # Moisture present, some risk
            'icy': (70, 90),     # Black ice confirmed
            'snow': (60, 80)     # Snow/ice confirmed
        }
        
        predicted_bifi = prediction.get('bifi_score', 50)
        actual_range = actual_bifi_range.get(actual, (40, 60))
        actual_center = (actual_range[0] + actual_range[1]) / 2
        
        # Calculate error
        error = predicted_bifi - actual_center
        
        # Store for calibration
        self.accuracy_history.append({
            'timestamp': datetime.now().isoformat(),
            'predicted': predicted_bifi,
            'actual': actual,
            'actual_center': actual_center,
            'error': error,
            'weather': weather
        })
        
        # Recalibrate if we have enough data
        if len(self.accuracy_history) >= 10:
            self._recalibrate_weights()
        
        # Save to disk
        self._save_calibration()
        
        logger.info(f"Learned from feedback: predicted={predicted_bifi:.1f}, actual={actual}, error={error:.1f}")
    
    def _recalibrate_weights(self):
        """Adjust component weights based on prediction accuracy"""
        if len(self.accuracy_history) < 10:
            return
        
        # Simple gradient descent on weights
        learning_rate = 0.01
        recent = self.accuracy_history[-50:]  # Use last 50 reports
        
        total_error = sum(abs(r['error']) for r in recent)
        avg_error = total_error / len(recent)
        
        # If average error is high, adjust weights slightly
        if avg_error > 20:
            # Increase weight on temperature (most reliable)
            self.weights['temperature'] = min(0.40, self.weights['temperature'] + learning_rate)
            
            # Decrease weight on less reliable factors
            self.weights['time'] = max(0.05, self.weights['time'] - learning_rate/2)
            
            # Normalize weights to sum to 1.0
            total = sum(self.weights.values())
            self.weights = {k: v/total for k, v in self.weights.items()}
            
            logger.info(f"Recalibrated weights after {len(recent)} reports (avg error: {avg_error:.1f})")
    
    def _calculate_confidence(self, weather_data: Dict) -> float:
        """
        Calculate prediction confidence based on historical accuracy
        in similar conditions
        """
        if len(self.accuracy_history) < 5:
            return 0.7  # Default moderate confidence
        
        # Find similar historical conditions
        temp = weather_data.get('temperature', 32)
        humidity = weather_data.get('humidity', 70)
        
        similar = [
            r for r in self.accuracy_history[-100:]  # Last 100 reports
            if abs(r['weather'].get('temperature', 32) - temp) < 5
            and abs(r['weather'].get('humidity', 70) - humidity) < 15
        ]
        
        if len(similar) < 3:
            return 0.65  # Low confidence, few similar cases
        
        # Calculate accuracy on similar cases
        errors = [abs(r['error']) for r in similar]
        avg_error = sum(errors) / len(errors)
        
        # Convert error to confidence (lower error = higher confidence)
        confidence = max(0.3, min(0.95, 1.0 - (avg_error / 100)))
        
        return confidence
    
    def _generate_explanation(self, bifi: float, components: Dict, 
                             temp: float, surface_temp: float,
                             humidity: float, wind: float, 
                             is_bridge: bool, confidence: float) -> str:
        """Generate clear, user-friendly explanation"""
        
        lines = []
        
        # Main risk assessment
        if bifi >= 80:
            lines.append("⚠️ EXTREME DANGER: Black ice highly likely")
            lines.append("DO NOT DRIVE if possible. Roads are treacherous.")
        elif bifi >= 60:
            lines.append("🚨 HIGH RISK: Black ice probable")
            lines.append("Drive only if necessary. Reduce speed by 50%.")
        elif bifi >= 40:
            lines.append("⚡ MODERATE RISK: Black ice possible")
            lines.append("Drive carefully, increase following distance.")
        elif bifi >= 20:
            lines.append("⚠️ LOW RISK: Conditions improving")
            lines.append("Stay alert for unexpected icy patches.")
        else:
            lines.append("✅ MINIMAL RISK: Conditions favorable")
            lines.append("Normal driving conditions expected.")
        
        lines.append("")
        
        # Key factors
        lines.append("Key factors:")
        
        if surface_temp < 32:
            lines.append(f"• Road surface at {surface_temp:.0f}°F (FREEZING)")
        else:
            lines.append(f"• Road surface: {surface_temp:.0f}°F")
        
        if temp <= 32 and humidity > 70:
            lines.append(f"• High humidity ({humidity:.0f}%) + freezing temps")
        
        if wind > 15:
            lines.append(f"• High winds ({wind:.0f} mph) increase risk")
        
        if is_bridge:
            lines.append("• BRIDGE/OVERPASS - freezes faster!")
        
        # Confidence indicator
        lines.append("")
        if confidence > 0.8:
            lines.append(f"📊 High confidence ({int(confidence*100)}%) - {len(self.accuracy_history)} verified reports")
        elif confidence > 0.6:
            lines.append(f"📊 Moderate confidence ({int(confidence*100)}%)")
        else:
            lines.append(f"📊 Limited data ({int(confidence*100)}%) - use caution")
        
        return "\n".join(lines)
    
    def _confidence_text(self, confidence: float) -> str:
        """Convert confidence to text"""
        if confidence > 0.85:
            return "Very High"
        elif confidence > 0.70:
            return "High"
        elif confidence > 0.55:
            return "Moderate"
        else:
            return "Low"
    
    def _should_warn(self, bifi: float, hours_ahead: int) -> Optional[str]:
        """Determine if user should be warned"""
        if bifi >= 80:
            return f"⚠️ EXTREME danger in {hours_ahead}h"
        elif bifi >= 60 and hours_ahead <= 3:
            return f"🚨 HIGH risk in {hours_ahead}h"
        return None
    
    def _load_calibration(self):
        """Load historical accuracy data"""
        try:
            if self.feedback_file.exists():
                with open(self.feedback_file, 'r') as f:
                    data = json.load(f)
                    self.accuracy_history = data.get('accuracy_history', [])
                    
                    # Load calibrated weights if available
                    if 'calibrated_weights' in data:
                        self.weights = data['calibrated_weights']
                        
                logger.info(f"Loaded {len(self.accuracy_history)} historical reports")
        except Exception as e:
            logger.error(f"Error loading calibration: {e}")
            self.accuracy_history = []
    
    def _save_calibration(self):
        """Save calibration data"""
        try:
            self.feedback_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.feedback_file, 'w') as f:
                json.dump({
                    'version': self.version,
                    'calibrated_weights': self.weights,
                    'accuracy_history': self.accuracy_history[-500:],  # Keep last 500
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving calibration: {e}")
    
    # Component calculation methods (same as v2)
    def _temp_component(self, air: float, surface: float) -> float:
        """Temperature risk score"""
        if surface < 28:
            return 100
        elif surface < 32:
            return 80 + ((32 - surface) * 5)
        elif surface < 36:
            return 60 + ((36 - surface) * 5)
        else:
            return max(0, 40 - ((surface - 36) * 2))
    
    def _humidity_component(self, humidity: float) -> float:
        """Humidity contribution"""
        if humidity > 90:
            return 100
        elif humidity > 80:
            return 80
        elif humidity > 70:
            return 60
        else:
            return max(0, humidity - 30)
    
    def _dew_point_component(self, temp: float, dew: float) -> float:
        """Dew point spread"""
        spread = temp - dew
        if spread < 2:
            return 100
        elif spread < 5:
            return 70
        else:
            return max(0, 50 - spread * 3)
    
    def _wind_component(self, wind: float, temp: float) -> float:
        """Wind effect"""
        if temp < 32:
            return max(0, 100 - wind * 2)  # More wind = more drying
        else:
            return 50
    
    def _time_component(self, hour: int) -> float:
        """Time of day effect"""
        if 3 <= hour <= 7:
            return 100  # Coldest time
        elif 0 <= hour <= 9 or 21 <= hour <= 23:
            return 70
        else:
            return 30
    
    def _precip_component(self, precip: float, temp: float) -> float:
        """Recent precipitation"""
        if precip > 0 and temp <= 35:
            return min(100, 80 + precip * 10)
        elif precip > 0:
            return 60
        return 30
    
    def _estimate_dew_point(self, temp_f: float, humidity: float) -> float:
        """Estimate dew point"""
        temp_c = (temp_f - 32) * 5/9
        rh = humidity / 100.0
        a, b = 17.27, 237.7
        alpha = ((a * temp_c) / (b + temp_c)) + np.log(rh)
        dew_c = (b * alpha) / (a - alpha)
        return (dew_c * 9/5) + 32
    
    def _get_risk_level(self, bifi: float) -> Tuple[str, str]:
        """Risk level and color"""
        if bifi >= 80:
            return "EXTREME", "#991b1b"
        elif bifi >= 60:
            return "HIGH", "#dc2626"
        elif bifi >= 40:
            return "MODERATE", "#f59e0b"
        elif bifi >= 20:
            return "LOW", "#eab308"
        else:
            return "MINIMAL", "#10b981"
