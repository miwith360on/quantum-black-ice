"""
Overnight Cooling Predictor
Predicts when roads will freeze based on overnight temperature drops
Critical for 2-6 AM window when radiative cooling is strongest
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import math

logger = logging.getLogger(__name__)

class OvernightCoolingPredictor:
    """Predict overnight temperature drops and freeze timing"""
    
    def __init__(self):
        logger.info("Overnight Cooling Predictor initialized")
    
    def predict_freeze_time(
        self,
        current_temp_f: float,
        current_time: datetime,
        dew_point_f: float,
        wind_speed_mph: float,
        cloud_cover_percent: float = 0
    ) -> Dict:
        """
        Predict when temperature will drop to freezing overnight
        
        Args:
            current_temp_f: Current air temperature
            current_time: Current datetime
            dew_point_f: Dew point temperature
            wind_speed_mph: Wind speed (higher = slower cooling)
            cloud_cover_percent: Cloud cover 0-100 (higher = slower cooling)
            
        Returns:
            {
                'will_freeze_tonight': bool,
                'freeze_time': datetime or None,
                'hours_until_freeze': float or None,
                'minimum_temp_f': float,
                'cooling_rate_per_hour': float,
                'risk_level': str,
                'warning_message': str
            }
        """
        
        # Calculate hours until sunrise (cooling stops at sunrise)
        hours_until_sunrise = self._hours_until_sunrise(current_time)
        
        # Calculate cooling rate based on conditions
        cooling_rate = self._calculate_cooling_rate(
            wind_speed_mph,
            cloud_cover_percent,
            current_time.hour
        )
        
        # Predict minimum overnight temperature
        predicted_min_temp = self._predict_minimum_temp(
            current_temp_f,
            dew_point_f,
            cooling_rate,
            hours_until_sunrise
        )
        
        # Will it freeze?
        will_freeze = predicted_min_temp <= 32.0
        
        # Calculate when freezing will occur
        freeze_time = None
        hours_until_freeze = None
        
        if will_freeze and current_temp_f > 32.0:
            # Calculate hours until temp drops to 32°F
            temp_drop_needed = current_temp_f - 32.0
            hours_until_freeze = temp_drop_needed / cooling_rate
            
            # Only predict if freeze happens before sunrise
            if hours_until_freeze <= hours_until_sunrise:
                freeze_time = current_time + timedelta(hours=hours_until_freeze)
            else:
                will_freeze = False  # Won't freeze before sunrise
        
        # Determine risk level
        risk_level, warning = self._calculate_risk_level(
            will_freeze,
            hours_until_freeze,
            predicted_min_temp,
            current_time
        )
        
        return {
            'will_freeze_tonight': will_freeze,
            'freeze_time': freeze_time.isoformat() if freeze_time else None,
            'freeze_time_display': self._format_freeze_time(freeze_time) if freeze_time else None,
            'hours_until_freeze': round(hours_until_freeze, 1) if hours_until_freeze else None,
            'minimum_temp_f': round(predicted_min_temp, 1),
            'current_temp_f': current_temp_f,
            'cooling_rate_per_hour': round(cooling_rate, 2),
            'hours_until_sunrise': round(hours_until_sunrise, 1),
            'risk_level': risk_level,
            'warning_message': warning,
            'is_critical_window': self._is_critical_window(current_time)
        }
    
    def _calculate_cooling_rate(
        self,
        wind_speed_mph: float,
        cloud_cover_percent: float,
        current_hour: int
    ) -> float:
        """
        Calculate overnight cooling rate in °F per hour
        
        Factors:
        - Clear skies = faster cooling (radiative heat loss)
        - Wind = slower cooling (mixing warm/cold air)
        - 2-6 AM = peak cooling (lowest sun angle)
        """
        
        # Base cooling rate (clear, calm night)
        base_rate = 3.0  # °F per hour
        
        # Cloud cover reduction (clouds trap heat)
        cloud_factor = 1.0 - (cloud_cover_percent / 100.0 * 0.6)
        # 100% clouds = 40% slower cooling
        
        # Wind reduction (wind prevents radiative cooling)
        if wind_speed_mph > 15:
            wind_factor = 0.5  # High wind = 50% slower cooling
        elif wind_speed_mph > 8:
            wind_factor = 0.7  # Moderate wind = 30% slower
        elif wind_speed_mph > 3:
            wind_factor = 0.85  # Light wind = 15% slower
        else:
            wind_factor = 1.0  # Calm = full cooling rate
        
        # Time of night factor (2-6 AM cools fastest)
        if 2 <= current_hour <= 6:
            time_factor = 1.3  # Peak cooling window
        elif 22 <= current_hour <= 24 or 0 <= current_hour <= 1:
            time_factor = 1.1  # Early night
        elif 7 <= current_hour <= 8:
            time_factor = 0.7  # Near sunrise
        else:
            time_factor = 0.5  # Daytime/evening
        
        cooling_rate = base_rate * cloud_factor * wind_factor * time_factor
        
        return max(cooling_rate, 0.5)  # Minimum 0.5°F/hour
    
    def _predict_minimum_temp(
        self,
        current_temp_f: float,
        dew_point_f: float,
        cooling_rate: float,
        hours_until_sunrise: float
    ) -> float:
        """
        Predict minimum overnight temperature
        
        Temperature rarely drops below dew point (condensation releases heat)
        """
        # Calculate temperature after overnight cooling
        total_cooling = cooling_rate * hours_until_sunrise
        predicted_temp = current_temp_f - total_cooling
        
        # Temperature floor = dew point (rarely goes below)
        minimum_temp = max(predicted_temp, dew_point_f - 2)
        # Allow up to 2°F below dew point in very dry conditions
        
        return minimum_temp
    
    def _hours_until_sunrise(self, current_time: datetime) -> float:
        """
        Calculate hours until sunrise (simplified)
        Assumes sunrise ~7 AM local time
        """
        current_hour = current_time.hour + current_time.minute / 60.0
        sunrise_hour = 7.0
        
        if current_hour < sunrise_hour:
            # Same day sunrise
            return sunrise_hour - current_hour
        else:
            # Next day sunrise
            return (24 - current_hour) + sunrise_hour
    
    def _is_critical_window(self, current_time: datetime) -> bool:
        """Check if currently in 2-6 AM critical cooling window"""
        return 2 <= current_time.hour <= 6
    
    def _calculate_risk_level(
        self,
        will_freeze: bool,
        hours_until_freeze: Optional[float],
        min_temp: float,
        current_time: datetime
    ) -> tuple:
        """Determine risk level and warning message"""
        
        if not will_freeze:
            return (
                'low',
                f"✅ No freeze expected tonight. Minimum temp: {min_temp:.1f}°F"
            )
        
        if hours_until_freeze is None:
            return (
                'low',
                f"Temperature will reach {min_temp:.1f}°F but not freeze"
            )
        
        # Already freezing
        if hours_until_freeze <= 0:
            return (
                'critical',
                f"🚨 FREEZING NOW! Temperature at or below 32°F"
            )
        
        # Freeze very soon
        if hours_until_freeze <= 1:
            freeze_minutes = int(hours_until_freeze * 60)
            return (
                'critical',
                f"⚠️ CRITICAL: Roads will freeze in {freeze_minutes} minutes!"
            )
        
        # Freeze within 2 hours
        if hours_until_freeze <= 2:
            return (
                'high',
                f"🔴 HIGH RISK: Roads will freeze in {hours_until_freeze:.1f} hours"
            )
        
        # Freeze within critical window (2-6 AM)
        freeze_hour = (current_time + timedelta(hours=hours_until_freeze)).hour
        if 2 <= freeze_hour <= 6:
            return (
                'high',
                f"🟡 Roads will freeze at {self._format_hour(freeze_hour)} (peak cooling window)"
            )
        
        # Freeze later tonight
        return (
            'moderate',
            f"⚠️ MODERATE: Roads will freeze in {hours_until_freeze:.1f} hours"
        )
    
    def _format_freeze_time(self, freeze_time: datetime) -> str:
        """Format freeze time for display"""
        return freeze_time.strftime("%-I:%M %p").lower()
    
    def _format_hour(self, hour: int) -> str:
        """Format hour for display (e.g., '4 AM')"""
        if hour == 0:
            return "12 AM"
        elif hour < 12:
            return f"{hour} AM"
        elif hour == 12:
            return "12 PM"
        else:
            return f"{hour - 12} PM"
    
    def get_hourly_cooling_forecast(
        self,
        current_temp_f: float,
        dew_point_f: float,
        wind_speed_mph: float,
        cloud_cover_percent: float,
        hours: int = 12
    ) -> List[Dict]:
        """
        Get hour-by-hour temperature forecast through the night
        
        Returns list of hourly predictions
        """
        current_time = datetime.now()
        forecast = []
        
        temp = current_temp_f
        
        for hour in range(hours):
            forecast_time = current_time + timedelta(hours=hour)
            
            # Calculate cooling rate for this hour
            cooling_rate = self._calculate_cooling_rate(
                wind_speed_mph,
                cloud_cover_percent,
                forecast_time.hour
            )
            
            # Don't drop below dew point
            temp = max(temp - cooling_rate, dew_point_f - 2)
            
            forecast.append({
                'hour': forecast_time.hour,
                'time_display': self._format_hour(forecast_time.hour),
                'temperature_f': round(temp, 1),
                'is_freezing': temp <= 32.0,
                'cooling_rate': round(cooling_rate, 2),
                'is_critical_window': 2 <= forecast_time.hour <= 6
            })
        
        return forecast
