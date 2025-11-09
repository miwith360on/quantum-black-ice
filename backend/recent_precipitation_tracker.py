"""
Recent Precipitation Tracker
Tracks recent rain/snow to detect wet pavement risk
Wet roads + freezing temp = instant black ice
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import requests

logger = logging.getLogger(__name__)

class RecentPrecipitationTracker:
    """Track recent precipitation to assess wet pavement risk"""
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = 600  # 10 minutes
        logger.info("Recent Precipitation Tracker initialized")
    
    def check_recent_precipitation(
        self,
        lat: float,
        lon: float,
        hours_back: int = 6
    ) -> Dict:
        """
        Check if it rained/snowed recently at this location
        
        Args:
            lat: Latitude
            lon: Longitude  
            hours_back: How many hours to look back (default 6)
            
        Returns:
            {
                'had_recent_precipitation': bool,
                'hours_since_precip': float or None,
                'precipitation_type': 'rain' | 'snow' | 'mixed' | 'none',
                'amount_inches': float,
                'pavement_likely_wet': bool,
                'black_ice_risk_multiplier': float,  # 1.0 = normal, 2.0 = double risk
                'warning_message': str
            }
        """
        
        cache_key = f"{lat:.4f},{lon:.4f}"
        
        # Check cache
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if (datetime.now().timestamp() - cached_time) < self.cache_duration:
                return cached_data
        
        try:
            # Get recent precipitation from Open-Meteo (free, no API key)
            precip_data = self._fetch_recent_precipitation(lat, lon, hours_back)
            
            # Calculate wet pavement risk
            result = self._analyze_precipitation_risk(precip_data, hours_back)
            
            # Cache result
            self.cache[cache_key] = (datetime.now().timestamp(), result)
            
            return result
            
        except Exception as e:
            logger.error(f"Recent precipitation check error: {e}")
            return self._default_response()
    
    def _fetch_recent_precipitation(
        self,
        lat: float,
        lon: float,
        hours_back: int
    ) -> Dict:
        """
        Fetch recent precipitation data from Open-Meteo API
        Free API, no key required
        """
        
        url = "https://api.open-meteo.com/v1/forecast"
        
        params = {
            'latitude': lat,
            'longitude': lon,
            'hourly': 'precipitation,rain,snowfall,temperature_2m',
            'past_hours': hours_back,
            'forecast_hours': 1,
            'temperature_unit': 'fahrenheit',
            'precipitation_unit': 'inch'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            logger.warning(f"Open-Meteo API error: {response.status_code}")
            return {}
        
        return response.json()
    
    def _analyze_precipitation_risk(self, data: Dict, hours_back: int) -> Dict:
        """Analyze precipitation data to assess black ice risk"""
        
        if not data or 'hourly' not in data:
            return self._default_response()
        
        hourly = data['hourly']
        precipitation = hourly.get('precipitation', [])
        rain = hourly.get('rain', [])
        snowfall = hourly.get('snowfall', [])
        temperatures = hourly.get('temperature_2m', [])
        times = hourly.get('time', [])
        
        if not precipitation:
            return self._default_response()
        
        # Find most recent precipitation
        total_precip = 0.0
        total_rain = 0.0
        total_snow = 0.0
        last_precip_hour = None
        
        for i in range(len(precipitation)):
            if precipitation[i] > 0:
                total_precip += precipitation[i]
                total_rain += rain[i] if i < len(rain) else 0
                total_snow += snowfall[i] if i < len(snowfall) else 0
                
                if last_precip_hour is None:
                    last_precip_hour = i
        
        # No recent precipitation
        if total_precip == 0:
            return {
                'had_recent_precipitation': False,
                'hours_since_precip': None,
                'precipitation_type': 'none',
                'amount_inches': 0.0,
                'pavement_likely_wet': False,
                'black_ice_risk_multiplier': 1.0,
                'warning_message': '✅ No recent precipitation. Roads likely dry.',
                'evaporation_status': 'dry'
            }
        
        # Calculate hours since last precipitation
        hours_since = hours_back - last_precip_hour if last_precip_hour is not None else hours_back
        
        # Determine precipitation type
        if total_rain > total_snow:
            precip_type = 'rain'
        elif total_snow > total_rain:
            precip_type = 'snow'
        else:
            precip_type = 'mixed'
        
        # Assess if pavement is still wet
        pavement_wet = self._is_pavement_wet(
            hours_since,
            total_precip,
            temperatures[-1] if temperatures else 32
        )
        
        # Calculate black ice risk multiplier
        risk_multiplier = self._calculate_risk_multiplier(
            pavement_wet,
            precip_type,
            total_precip,
            hours_since
        )
        
        # Generate warning
        warning = self._generate_warning(
            pavement_wet,
            precip_type,
            hours_since,
            risk_multiplier
        )
        
        return {
            'had_recent_precipitation': True,
            'hours_since_precip': round(hours_since, 1),
            'precipitation_type': precip_type,
            'amount_inches': round(total_precip, 2),
            'pavement_likely_wet': pavement_wet,
            'black_ice_risk_multiplier': round(risk_multiplier, 1),
            'warning_message': warning,
            'evaporation_status': self._get_evaporation_status(hours_since, pavement_wet),
            'total_rain_inches': round(total_rain, 2),
            'total_snow_inches': round(total_snow, 2)
        }
    
    def _is_pavement_wet(
        self,
        hours_since_precip: float,
        total_precip_inches: float,
        current_temp_f: float
    ) -> bool:
        """
        Determine if pavement is still wet
        
        Factors:
        - Recent heavy rain = definitely wet
        - Light rain hours ago = probably dry
        - Temperature affects evaporation rate
        """
        
        # Heavy recent precipitation = definitely wet
        if hours_since_precip < 1 and total_precip_inches > 0.05:
            return True
        
        # Calculate evaporation time based on temperature
        if current_temp_f > 60:
            evap_hours = 2  # Fast evaporation
        elif current_temp_f > 40:
            evap_hours = 4  # Moderate evaporation
        elif current_temp_f > 32:
            evap_hours = 6  # Slow evaporation
        else:
            evap_hours = 12  # Very slow/no evaporation below freezing
        
        # Adjust for precipitation amount
        evap_hours *= min(total_precip_inches / 0.1, 3.0)  # More rain = longer to dry
        
        return hours_since_precip < evap_hours
    
    def _calculate_risk_multiplier(
        self,
        pavement_wet: bool,
        precip_type: str,
        amount: float,
        hours_since: float
    ) -> float:
        """
        Calculate black ice risk multiplier
        
        Wet pavement + freezing = MUCH higher black ice risk
        """
        
        if not pavement_wet:
            return 1.0  # Normal risk
        
        # Base multiplier for wet pavement
        base_multiplier = 2.0
        
        # Recent heavy precipitation = higher risk
        if hours_since < 2 and amount > 0.1:
            base_multiplier = 3.0  # Triple risk!
        
        # Snow creates slush which freezes into ice
        if precip_type == 'snow' and amount > 0.5:
            base_multiplier *= 1.3
        
        return base_multiplier
    
    def _generate_warning(
        self,
        wet: bool,
        precip_type: str,
        hours_since: float,
        multiplier: float
    ) -> str:
        """Generate user-friendly warning message"""
        
        if not wet:
            return f"✅ Roads likely dry ({hours_since:.1f} hours since {precip_type})"
        
        if multiplier >= 3.0:
            return (
                f"🚨 CRITICAL: Heavy {precip_type} {hours_since:.1f} hours ago. "
                f"Roads still WET. Black ice risk {multiplier:.1f}x HIGHER if temp drops!"
            )
        elif multiplier >= 2.0:
            return (
                f"⚠️ WARNING: Recent {precip_type} ({hours_since:.1f}h ago). "
                f"Wet pavement = {multiplier:.1f}x higher freeze risk!"
            )
        else:
            return (
                f"🟡 Recent {precip_type}, pavement drying. "
                f"Monitor for puddles/wet spots."
            )
    
    def _get_evaporation_status(self, hours_since: float, still_wet: bool) -> str:
        """Get evaporation status description"""
        if not still_wet:
            return 'evaporated'
        elif hours_since < 1:
            return 'very_wet'
        elif hours_since < 3:
            return 'wet'
        else:
            return 'drying'
    
    def _default_response(self) -> Dict:
        """Return default response when API fails"""
        return {
            'had_recent_precipitation': False,
            'hours_since_precip': None,
            'precipitation_type': 'unknown',
            'amount_inches': 0.0,
            'pavement_likely_wet': False,
            'black_ice_risk_multiplier': 1.0,
            'warning_message': 'Unable to determine recent precipitation',
            'evaporation_status': 'unknown'
        }
