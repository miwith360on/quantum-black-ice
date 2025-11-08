"""
Black Ice Formation Index (BIFI)
Proprietary metric for black ice risk assessment
Like "Wind Chill" but specifically for black ice conditions
"""

import numpy as np
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BlackIceFormationIndex:
    """
    Calculate BIFI score (0-100) representing black ice formation risk
    
    BIFI Scale:
    0-20:   Minimal Risk (Green)
    21-40:  Low Risk (Yellow-Green)
    41-60:  Moderate Risk (Yellow)
    61-80:  High Risk (Orange)
    81-100: Extreme Risk (Red)
    
    Formula considers:
    - Air temperature
    - Road surface temperature
    - Dew point
    - Humidity
    - Wind speed (wind chill effect)
    - Time of day (radiative cooling)
    - Precipitation
    """
    
    def __init__(self):
        self.version = "1.0.0"
        logger.info(f"BIFI Calculator initialized (v{self.version})")
        
    def calculate(self, weather_data):
        """
        Calculate Black Ice Formation Index
        
        Args:
            weather_data: Dict containing:
                - temperature: Air temp (F)
                - surface_temp: Road surface temp (F) [optional]
                - humidity: Relative humidity (%)
                - dew_point: Dew point temp (F) [optional]
                - wind_speed: Wind speed (mph)
                - precipitation: Recent precip (mm) [optional]
                - time: Datetime object [optional]
        
        Returns:
            Dict with BIFI score and detailed breakdown
        """
        temp = weather_data.get('temperature', 32)
        humidity = weather_data.get('humidity', 70)
        wind_speed = weather_data.get('wind_speed', 5)
        
        # Calculate or extract optional parameters
        surface_temp = weather_data.get('surface_temp', temp - 5)  # Estimate if not provided
        dew_point = weather_data.get('dew_point', self._calculate_dew_point(temp, humidity))
        precipitation = weather_data.get('precipitation', 0)
        time = weather_data.get('time', datetime.now())
        
        # Component scores (each 0-100)
        temp_score = self._temperature_component(temp, surface_temp)
        humidity_score = self._humidity_component(humidity)
        dew_point_score = self._dew_point_component(temp, dew_point)
        wind_score = self._wind_component(wind_speed, temp)
        time_score = self._time_component(time)
        precip_score = self._precipitation_component(precipitation, temp)
        
        # Weighted combination
        weights = {
            'temperature': 0.30,      # Most important
            'humidity': 0.20,
            'dew_point': 0.20,
            'wind': 0.15,
            'time': 0.10,
            'precipitation': 0.05
        }
        
        bifi_score = (
            temp_score * weights['temperature'] +
            humidity_score * weights['humidity'] +
            dew_point_score * weights['dew_point'] +
            wind_score * weights['wind'] +
            time_score * weights['time'] +
            precip_score * weights['precipitation']
        )
        
        # Apply surface temperature amplification
        if surface_temp < 32:
            bifi_score *= 1.25  # 25% increase if surface already freezing
        
        # Cap at 100
        bifi_score = min(bifi_score, 100)
        
        # Get risk category
        category = self._get_risk_category(bifi_score)
        
        logger.info(f"BIFI calculated: {bifi_score:.1f} ({category['level']})")
        
        return {
            'bifi_score': round(bifi_score, 1),
            'risk_level': category['level'],
            'risk_color': category['color'],
            'risk_description': category['description'],
            'components': {
                'temperature': round(temp_score, 1),
                'humidity': round(humidity_score, 1),
                'dew_point': round(dew_point_score, 1),
                'wind': round(wind_score, 1),
                'time_of_day': round(time_score, 1),
                'precipitation': round(precip_score, 1)
            },
            'conditions': {
                'air_temp': round(temp, 1),
                'surface_temp': round(surface_temp, 1),
                'dew_point': round(dew_point, 1),
                'humidity': round(humidity, 1),
                'wind_speed': round(wind_speed, 1)
            },
            'timestamp': datetime.now().isoformat(),
            'version': self.version
        }
    
    def _temperature_component(self, air_temp, surface_temp):
        """
        Temperature risk score (0-100)
        Higher score = more risk
        
        Peak risk: surface temp 28-32°F (just at freezing)
        """
        # Use surface temp as primary indicator
        if surface_temp <= 28:
            # Very cold - ice will form quickly
            return 100
        elif surface_temp <= 32:
            # At freezing point - highest black ice risk
            return 95
        elif surface_temp <= 35:
            # Just above freezing - still risky
            return 70
        elif surface_temp <= 40:
            # Cool but less likely to freeze
            return 40
        elif surface_temp <= 50:
            # Minimal risk
            return 15
        else:
            # No risk
            return 0
    
    def _humidity_component(self, humidity):
        """
        Humidity risk score (0-100)
        Higher humidity = more moisture = more ice potential
        """
        if humidity >= 90:
            return 100
        elif humidity >= 80:
            return 85
        elif humidity >= 70:
            return 65
        elif humidity >= 60:
            return 45
        elif humidity >= 50:
            return 25
        else:
            return 10
    
    def _dew_point_component(self, temp, dew_point):
        """
        Dew point spread risk score
        When temp is close to dew point, condensation likely
        """
        spread = temp - dew_point
        
        if spread <= 2:
            # Very close - high condensation risk
            return 100
        elif spread <= 5:
            # Close - moderate condensation
            return 75
        elif spread <= 10:
            # Some condensation possible
            return 40
        else:
            # Dry conditions
            return 10
    
    def _wind_component(self, wind_speed, temp):
        """
        Wind effect on ice formation
        Light wind = ideal for black ice
        Strong wind = evaporates moisture
        """
        # Calculate wind chill effect
        if temp <= 50 and wind_speed >= 3:
            wind_chill = 35.74 + 0.6215*temp - 35.75*(wind_speed**0.16) + 0.4275*temp*(wind_speed**0.16)
            chill_diff = temp - wind_chill
        else:
            chill_diff = 0
        
        # Light wind (3-8 mph) is worst - causes evaporative cooling without drying
        if 3 <= wind_speed <= 8:
            base_score = 80
        elif wind_speed < 3:
            # Calm - less evaporative cooling
            base_score = 60
        elif wind_speed <= 15:
            # Moderate - some drying effect
            base_score = 50
        else:
            # Strong wind - dries roads
            base_score = 20
        
        # Add wind chill contribution
        wind_chill_score = min(chill_diff * 2, 20)  # Up to 20 points from chill
        
        return base_score + wind_chill_score
    
    def _time_component(self, time):
        """
        Time of day risk
        Highest risk: 4-8 AM (overnight radiative cooling)
        """
        hour = time.hour
        
        # 4-8 AM: Peak risk (overnight cooling)
        if 4 <= hour < 8:
            return 100
        # 8-10 AM: Still risky (sun not strong yet)
        elif 8 <= hour < 10:
            return 70
        # 10 PM - 4 AM: Building risk (cooling down)
        elif hour >= 22 or hour < 4:
            return 80
        # 6-9 PM: Sunset, starting to cool
        elif 18 <= hour < 21:
            return 60
        # Daytime: Lower risk (sun warming roads)
        else:
            return 20
    
    def _precipitation_component(self, precipitation, temp):
        """
        Recent precipitation risk
        Wet roads + cold = ice
        """
        if precipitation > 0 and temp <= 35:
            # Recent moisture + cold = high risk
            if precipitation >= 5:  # Heavy precip
                return 100
            elif precipitation >= 2:  # Moderate precip
                return 80
            else:  # Light precip
                return 60
        elif precipitation > 0:
            # Moisture present but not freezing
            return 30
        else:
            # No recent precipitation
            return 0
    
    def _calculate_dew_point(self, temp, humidity):
        """
        Estimate dew point from temperature and humidity
        Magnus formula (accurate to ±0.4°C)
        """
        # Convert F to C
        temp_c = (temp - 32) * 5/9
        
        # Magnus constants
        a = 17.27
        b = 237.7
        
        alpha = ((a * temp_c) / (b + temp_c)) + np.log(humidity / 100.0)
        dew_point_c = (b * alpha) / (a - alpha)
        
        # Convert back to F
        dew_point_f = (dew_point_c * 9/5) + 32
        
        return dew_point_f
    
    def _get_risk_category(self, bifi_score):
        """Map BIFI score to risk category"""
        if bifi_score >= 81:
            return {
                'level': 'EXTREME',
                'color': '#8B0000',  # Dark red
                'description': 'Black ice formation highly likely - Extreme danger'
            }
        elif bifi_score >= 61:
            return {
                'level': 'HIGH',
                'color': '#FF4500',  # Orange-red
                'description': 'High probability of black ice - Drive with extreme caution'
            }
        elif bifi_score >= 41:
            return {
                'level': 'MODERATE',
                'color': '#FFD700',  # Gold
                'description': 'Moderate black ice risk - Exercise caution'
            }
        elif bifi_score >= 21:
            return {
                'level': 'LOW',
                'color': '#9ACD32',  # Yellow-green
                'description': 'Low black ice risk - Monitor conditions'
            }
        else:
            return {
                'level': 'MINIMAL',
                'color': '#32CD32',  # Green
                'description': 'Minimal black ice risk - Roads likely safe'
            }
    
    def get_bifi_interpretation(self, bifi_score):
        """
        Get human-readable interpretation of BIFI score
        
        Returns:
            String with actionable advice
        """
        if bifi_score >= 81:
            return ("🔴 EXTREME RISK (BIFI {:.0f}/100): Black ice formation imminent. "
                   "Avoid driving if possible. If you must drive, reduce speed by 50% "
                   "and increase following distance to 8+ seconds.").format(bifi_score)
        elif bifi_score >= 61:
            return ("🟠 HIGH RISK (BIFI {:.0f}/100): Black ice likely on bridges, "
                   "overpasses, and shaded areas. Reduce speed, avoid sudden braking, "
                   "and allow extra travel time.").format(bifi_score)
        elif bifi_score >= 41:
            return ("🟡 MODERATE RISK (BIFI {:.0f}/100): Black ice possible in spots. "
                   "Exercise caution on bridges and in shaded areas. Drive defensively.").format(bifi_score)
        elif bifi_score >= 21:
            return ("🟢 LOW RISK (BIFI {:.0f}/100): Black ice unlikely but not impossible. "
                   "Remain alert, especially in early morning hours.").format(bifi_score)
        else:
            return ("✅ MINIMAL RISK (BIFI {:.0f}/100): Conditions not favorable for "
                   "black ice formation. Roads should be safe.").format(bifi_score)
