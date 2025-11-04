"""
Black Ice Prediction Engine
Analyzes weather conditions to predict black ice formation
"""

from typing import Dict, Optional
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk levels for black ice formation"""
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"


class BlackIcePredictor:
    """
    Predicts black ice formation based on weather conditions
    
    Black ice forms when:
    - Temperature is near or below freezing (0°C / 32°F)
    - High humidity or recent precipitation
    - Dew point is near surface temperature
    - Low wind speeds (allows ice to form)
    - Clear skies at night (radiational cooling)
    """
    
    # Critical temperature thresholds (Celsius)
    FREEZING_POINT = 0.0
    DANGER_TEMP_MIN = -5.0
    DANGER_TEMP_MAX = 2.0
    
    # Humidity threshold
    HIGH_HUMIDITY = 80.0
    
    # Wind speed threshold (m/s)
    LOW_WIND_SPEED = 3.0
    
    def predict(
        self,
        temperature: float,
        humidity: float,
        dew_point: float,
        wind_speed: float,
        precipitation: float = 0.0,
        road_temperature: Optional[float] = None
    ) -> Dict:
        """
        Predict black ice formation risk
        
        Args:
            temperature: Air temperature in Celsius
            humidity: Relative humidity (0-100)
            dew_point: Dew point temperature in Celsius
            wind_speed: Wind speed in m/s
            precipitation: Recent precipitation in mm
            road_temperature: Road surface temperature (if available)
            
        Returns:
            Dictionary with risk assessment
        """
        factors = []
        risk_score = 0.0
        
        # Use road temperature if available, otherwise use air temperature
        surface_temp = road_temperature if road_temperature is not None else temperature
        
        # Factor 1: Temperature near freezing
        if self.DANGER_TEMP_MIN <= surface_temp <= self.DANGER_TEMP_MAX:
            temp_factor = self._calculate_temperature_factor(surface_temp)
            risk_score += temp_factor
            factors.append({
                'name': 'Critical Temperature Range',
                'score': temp_factor,
                'description': f'Surface temperature {surface_temp:.1f}°C is in dangerous range'
            })
        
        # Factor 2: High humidity
        if humidity >= self.HIGH_HUMIDITY:
            humidity_factor = (humidity - self.HIGH_HUMIDITY) / 20.0 * 25
            risk_score += humidity_factor
            factors.append({
                'name': 'High Humidity',
                'score': humidity_factor,
                'description': f'Humidity at {humidity:.0f}% increases ice formation risk'
            })
        
        # Factor 3: Dew point near surface temperature
        temp_dewpoint_diff = abs(surface_temp - dew_point)
        if temp_dewpoint_diff < 3.0:
            dewpoint_factor = (3.0 - temp_dewpoint_diff) / 3.0 * 20
            risk_score += dewpoint_factor
            factors.append({
                'name': 'Temperature-Dewpoint Convergence',
                'score': dewpoint_factor,
                'description': 'Surface temperature near dew point promotes condensation'
            })
        
        # Factor 4: Low wind speeds
        if wind_speed < self.LOW_WIND_SPEED:
            wind_factor = (self.LOW_WIND_SPEED - wind_speed) / self.LOW_WIND_SPEED * 15
            risk_score += wind_factor
            factors.append({
                'name': 'Low Wind Speed',
                'score': wind_factor,
                'description': f'Light winds ({wind_speed:.1f} m/s) allow ice to form'
            })
        
        # Factor 5: Recent precipitation
        if precipitation > 0:
            precip_factor = min(precipitation * 10, 20)
            risk_score += precip_factor
            factors.append({
                'name': 'Recent Precipitation',
                'score': precip_factor,
                'description': f'{precipitation:.1f}mm precipitation provides moisture for ice'
            })
        
        # Calculate probability (0-100%)
        probability = min(risk_score, 100.0)
        
        # Determine risk level
        risk_level = self._determine_risk_level(probability)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(risk_level, factors)
        
        result = {
            'risk_level': risk_level.value,
            'probability': round(probability, 1),
            'risk_score': round(risk_score, 1),
            'factors': factors,
            'recommendations': recommendations,
            'conditions': {
                'temperature': temperature,
                'surface_temperature': surface_temp,
                'humidity': humidity,
                'dew_point': dew_point,
                'wind_speed': wind_speed,
                'precipitation': precipitation
            }
        }
        
        logger.info(f"Black ice prediction: {risk_level.value} ({probability:.1f}%)")
        return result
    
    def _calculate_temperature_factor(self, temperature: float) -> float:
        """Calculate risk factor based on temperature"""
        # Maximum risk at 0°C, decreasing as we move away
        if temperature < self.DANGER_TEMP_MIN or temperature > self.DANGER_TEMP_MAX:
            return 0.0
        
        # Distance from freezing point
        dist_from_zero = abs(temperature - self.FREEZING_POINT)
        max_distance = max(
            abs(self.DANGER_TEMP_MAX - self.FREEZING_POINT),
            abs(self.DANGER_TEMP_MIN - self.FREEZING_POINT)
        )
        
        # Inverse relationship: closer to 0°C = higher risk
        factor = (1.0 - (dist_from_zero / max_distance)) * 40
        return factor
    
    def _determine_risk_level(self, probability: float) -> RiskLevel:
        """Determine risk level based on probability"""
        if probability >= 80:
            return RiskLevel.EXTREME
        elif probability >= 60:
            return RiskLevel.HIGH
        elif probability >= 40:
            return RiskLevel.MODERATE
        elif probability >= 20:
            return RiskLevel.LOW
        else:
            return RiskLevel.NONE
    
    def _generate_recommendations(self, risk_level: RiskLevel, factors: list) -> list:
        """Generate safety recommendations based on risk level"""
        recommendations = []
        
        if risk_level == RiskLevel.EXTREME:
            recommendations.extend([
                "DANGER: Extreme black ice risk - avoid all non-essential travel",
                "Road surfaces extremely hazardous - expect ice on all surfaces",
                "If travel is unavoidable, reduce speed by 50% or more",
                "Increase following distance to 10+ seconds",
                "Alert emergency services to high-risk conditions"
            ])
        elif risk_level == RiskLevel.HIGH:
            recommendations.extend([
                "WARNING: High black ice risk - exercise extreme caution",
                "Reduce speed significantly and increase following distance",
                "Avoid bridges, overpasses, and shaded areas",
                "Keep emergency supplies in vehicle",
                "Consider delaying travel if possible"
            ])
        elif risk_level == RiskLevel.MODERATE:
            recommendations.extend([
                "CAUTION: Moderate black ice risk - drive carefully",
                "Watch for icy patches on bridges and shaded roads",
                "Reduce speed in areas prone to ice formation",
                "Maintain safe following distance"
            ])
        elif risk_level == RiskLevel.LOW:
            recommendations.extend([
                "Low risk but remain alert for isolated icy patches",
                "Monitor temperature changes, especially at night",
                "Use caution on bridges and overpasses"
            ])
        else:
            recommendations.append("Conditions not conducive to black ice formation")
        
        return recommendations
