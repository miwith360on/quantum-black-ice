"""
Physics + ML Hybrid BIFI Calculator
Splits risk into P(wet) × P(freeze) × bridge_multiplier with explainable physics
"""

import numpy as np
import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class HybridBIFI:
    """
    Advanced BIFI using physics-based probability decomposition
    
    Risk = P(surface_wet) × P(surface_freeze) × bridge_multiplier × uncertainty_adjustment
    
    This makes predictions:
    - Explainable (can debug which component failed)
    - Calibratable (adjust each probability independently)
    - Accurate (physics constraints prevent impossible predictions)
    """
    
    def __init__(self):
        self.version = "2.0.0-hybrid"
        logger.info(f"Hybrid BIFI Calculator initialized (v{self.version})")
    
    def calculate(self, weather_data: Dict) -> Dict:
        """
        Calculate hybrid BIFI with explainable components
        
        Args:
            weather_data: Weather and road conditions
        
        Returns:
            Dict with probabilities, BIFI score, and explanations
        """
        # Extract features
        air_temp = weather_data.get('temperature', 32)
        surface_temp = weather_data.get('road_temperature', weather_data.get('surface_temp', air_temp - 3))
        humidity = weather_data.get('humidity', 70)
        dew_point = weather_data.get('dew_point', self._estimate_dew_point(air_temp, humidity))
        wind_speed = weather_data.get('wind_speed', 5)
        precipitation = weather_data.get('precipitation', 0)
        clouds = weather_data.get('clouds', 50)
        hour = weather_data.get('hour', datetime.now().hour)
        is_bridge = weather_data.get('is_bridge', False)
        
        # Calculate wet-bulb temperature for evaporative cooling
        wet_bulb = self._calculate_wet_bulb(air_temp, humidity, dew_point)
        
        # Calculate cooling rate (if temperature history available)
        cooling_rate = weather_data.get('cooling_rate', 0)
        
        # Component A: P(surface_wet) - Probability surface has moisture
        p_wet, wet_features = self._calculate_wetness_probability(
            precipitation, humidity, dew_point, air_temp, cooling_rate
        )
        
        # Component B: P(surface_freeze) - Probability surface is at/below freezing
        p_freeze, freeze_features = self._calculate_freeze_probability(
            surface_temp, air_temp, wind_speed, clouds, hour, wet_bulb, cooling_rate
        )
        
        # Component C: Bridge/overpass multiplier
        bridge_multiplier, bridge_reason = self._calculate_bridge_multiplier(
            is_bridge, wind_speed, surface_temp
        )
        
        # Component D: Uncertainty adjustment
        uncertainty_adjustment, uncertainty_reasons = self._calculate_uncertainty(
            weather_data, wet_features, freeze_features
        )
        
        # Combined risk
        base_risk = p_wet * p_freeze
        adjusted_risk = base_risk * bridge_multiplier * uncertainty_adjustment
        
        # Convert to BIFI score (0-100)
        bifi_score = min(100, adjusted_risk * 100)
        
        # Determine risk level
        risk_level, risk_color = self._get_risk_level(bifi_score)
        
        # Build explanation
        explanation = self._build_explanation(
            p_wet, p_freeze, bridge_multiplier, uncertainty_adjustment,
            wet_features, freeze_features, bridge_reason, uncertainty_reasons
        )
        
        return {
            'bifi_score': round(bifi_score, 1),
            'risk_level': risk_level,
            'risk_color': risk_color,
            'components': {
                'p_wet': round(p_wet, 3),
                'p_freeze': round(p_freeze, 3),
                'bridge_multiplier': round(bridge_multiplier, 2),
                'uncertainty_adjustment': round(uncertainty_adjustment, 2),
                'base_risk': round(base_risk, 3),
                'adjusted_risk': round(adjusted_risk, 3)
            },
            'features': {
                'wetness': wet_features,
                'freeze': freeze_features
            },
            'explanation': explanation,
            'version': self.version
        }
    
    def _calculate_wetness_probability(
        self, precip: float, humidity: float, dew_point: float, 
        air_temp: float, cooling_rate: float
    ) -> tuple[float, Dict]:
        """Calculate probability that road surface has moisture"""
        p_wet = 0.0
        features = {}
        
        # Recent precipitation (most direct indicator)
        if precip > 0:
            # More precip = higher probability
            p_precip = min(1.0, precip / 5.0)  # 5mm = 100% wet
            p_wet = max(p_wet, p_precip)
            features['precipitation'] = f"{precip}mm in last hour ({int(p_precip*100)}%)"
        
        # High humidity near saturation
        if humidity > 85:
            p_humidity = (humidity - 85) / 15.0  # 85-100% scaled to 0-1
            p_wet = max(p_wet, p_humidity)
            features['high_humidity'] = f"{humidity}% RH ({int(p_humidity*100)}%)"
        
        # Dew point close to air temp (condensation likely)
        dew_point_spread = air_temp - dew_point
        if dew_point_spread < 5:
            p_dew = 1.0 - (dew_point_spread / 5.0)  # <5°F = condensation
            p_wet = max(p_wet, p_dew * 0.7)  # Cap at 70% for dew alone
            features['dew_point_spread'] = f"{dew_point_spread:.1f}°F spread ({int(p_dew*100)}%)"
        
        # Rapid cooling (creates condensation)
        if cooling_rate < -3:  # Dropping >3°F/hour
            p_cooling = min(1.0, abs(cooling_rate) / 10.0)
            p_wet = max(p_wet, p_cooling * 0.5)
            features['rapid_cooling'] = f"{cooling_rate:.1f}°F/hr ({int(p_cooling*100)}%)"
        
        # If nothing indicates wetness, small baseline
        if p_wet == 0:
            p_wet = 0.05
            features['baseline'] = "No moisture indicators (5%)"
        
        return p_wet, features
    
    def _calculate_freeze_probability(
        self, surface_temp: float, air_temp: float, wind_speed: float,
        clouds: float, hour: int, wet_bulb: float, cooling_rate: float
    ) -> tuple[float, Dict]:
        """Calculate probability that road surface is at/below 32°F"""
        features = {}
        
        # Primary: Actual surface temperature
        if surface_temp <= 32:
            p_freeze = 1.0
            features['surface_temp'] = f"{surface_temp:.1f}°F (FREEZING)"
        elif surface_temp <= 35:
            # Linear transition 32-35°F
            p_freeze = 1.0 - ((surface_temp - 32) / 3.0)
            features['surface_temp'] = f"{surface_temp:.1f}°F (near freezing, {int(p_freeze*100)}%)"
        else:
            # Above 35°F, use physics model
            p_freeze = 0.0
            features['surface_temp'] = f"{surface_temp:.1f}°F (above freezing)"
            
            # Radiational cooling (clear night sky)
            if hour < 6 or hour > 20:  # Nighttime
                if clouds < 30:  # Clear skies
                    radiational_cooling = 3.0  # Can cool 3°F below air temp
                    effective_surface = surface_temp - radiational_cooling
                    if effective_surface <= 35:
                        p_freeze = 0.3
                        features['radiational_cooling'] = f"Clear night: {radiational_cooling}°F penalty"
            
            # Evaporative cooling (wet-bulb effect)
            if wet_bulb < surface_temp:
                evap_cooling = (surface_temp - wet_bulb) * 0.3
                effective_surface = surface_temp - evap_cooling
                if effective_surface <= 35:
                    p_freeze = max(p_freeze, 0.2)
                    features['evaporative_cooling'] = f"Wet-bulb {wet_bulb:.1f}°F (evaporation risk)"
            
            # Fast cooling trend
            if cooling_rate < -5:  # Dropping fast
                p_freeze = max(p_freeze, 0.3)
                features['cooling_trend'] = f"{cooling_rate:.1f}°F/hr (rapid drop)"
        
        return p_freeze, features
    
    def _calculate_bridge_multiplier(
        self, is_bridge: bool, wind_speed: float, surface_temp: float
    ) -> tuple[float, str]:
        """Bridges freeze faster - calculate multiplier"""
        if not is_bridge:
            return 1.0, "Not a bridge"
        
        # Bridges freeze earlier due to:
        # 1. Exposure on both sides (top and bottom)
        # 2. Wind chill effect more pronounced
        # 3. No ground thermal mass
        
        base_multiplier = 1.3  # 30% higher base risk
        
        # High wind increases bridge effect
        if wind_speed > 15:
            wind_bonus = 0.2
            reason = f"Bridge + high wind ({wind_speed:.0f} mph): {base_multiplier + wind_bonus:.1f}x risk"
            return base_multiplier + wind_bonus, reason
        
        reason = f"Bridge location: {base_multiplier}x risk"
        return base_multiplier, reason
    
    def _calculate_uncertainty(
        self, weather_data: Dict, wet_features: Dict, freeze_features: Dict
    ) -> tuple[float, list]:
        """Adjust confidence based on data quality and edge cases"""
        adjustment = 1.0
        reasons = []
        
        # Missing key sensors
        if 'road_temperature' not in weather_data and 'surface_temp' not in weather_data:
            adjustment *= 0.85
            reasons.append("No surface temp sensor (-15%)")
        
        # Transition conditions (hardest to predict)
        temp = weather_data.get('temperature', 32)
        if 30 <= temp <= 36:  # Critical transition zone
            adjustment *= 1.15
            reasons.append("Transition zone 30-36°F (+15% caution)")
        
        # Low confidence in wetness
        if len(wet_features) == 1 and 'baseline' in wet_features:
            adjustment *= 0.9
            reasons.append("Low wetness confidence (-10%)")
        
        return adjustment, reasons
    
    def _calculate_wet_bulb(self, air_temp: float, humidity: float, dew_point: float) -> float:
        """
        Simplified wet-bulb temperature calculation
        Wet-bulb is always between dew point and air temp
        """
        # Rough approximation using humidity
        rh_factor = humidity / 100.0
        wet_bulb = dew_point + (air_temp - dew_point) * (1 - rh_factor) * 0.3
        return wet_bulb
    
    def _estimate_dew_point(self, temp_f: float, humidity: float) -> float:
        """Estimate dew point if not provided"""
        temp_c = (temp_f - 32) * 5/9
        rh = humidity / 100.0
        
        # Magnus formula
        a, b = 17.27, 237.7
        alpha = ((a * temp_c) / (b + temp_c)) + np.log(rh)
        dew_c = (b * alpha) / (a - alpha)
        
        return (dew_c * 9/5) + 32
    
    def _get_risk_level(self, bifi_score: float) -> tuple[str, str]:
        """Map BIFI score to risk level"""
        if bifi_score >= 80:
            return "EXTREME", "#991b1b"
        elif bifi_score >= 60:
            return "HIGH", "#dc2626"
        elif bifi_score >= 40:
            return "MODERATE", "#f59e0b"
        elif bifi_score >= 20:
            return "LOW", "#eab308"
        else:
            return "MINIMAL", "#10b981"
    
    def _build_explanation(
        self, p_wet: float, p_freeze: float, bridge_mult: float, 
        uncertainty: float, wet_features: Dict, freeze_features: Dict,
        bridge_reason: str, uncertainty_reasons: list
    ) -> str:
        """Build human-readable explanation"""
        parts = []
        
        # Wetness
        parts.append(f"Surface wetness: {int(p_wet*100)}%")
        if wet_features:
            parts.append("  → " + ", ".join(wet_features.values()))
        
        # Freeze
        parts.append(f"Freeze probability: {int(p_freeze*100)}%")
        if freeze_features:
            parts.append("  → " + ", ".join(freeze_features.values()))
        
        # Bridge
        if bridge_mult > 1.0:
            parts.append(bridge_reason)
        
        # Uncertainty
        if uncertainty_reasons:
            parts.append("Adjustments: " + "; ".join(uncertainty_reasons))
        
        return "\n".join(parts)


# Backward compatibility - keep old BIFI available
class BlackIceFormationIndex(HybridBIFI):
    """Alias for backward compatibility"""
    pass
