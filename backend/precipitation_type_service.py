"""
Precipitation Type Detection Service
Uses NOAA Weather.gov API to detect freezing rain, sleet, snow, etc.
Critical for black ice prediction - freezing rain = instant black ice
"""

import requests
import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class PrecipitationTypeService:
    """Detect precipitation type using NOAA Weather.gov API (free, no key required)"""
    
    def __init__(self):
        self.base_url = "https://api.weather.gov"
        logger.info("Precipitation Type Service initialized (NOAA Weather.gov)")
    
    def get_precipitation_type(self, lat: float, lon: float) -> Dict:
        """
        Get current and forecasted precipitation type
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            {
                'current_type': 'freezing_rain' | 'sleet' | 'snow' | 'rain' | 'none',
                'intensity': 'light' | 'moderate' | 'heavy',
                'black_ice_risk': 'critical' | 'high' | 'moderate' | 'low',
                'forecast_next_hour': str,
                'temperature': float,
                'description': str
            }
        """
        try:
            # Get forecast data from NOAA
            forecast_data = self._get_forecast(lat, lon)
            
            if not forecast_data:
                return self._default_response()
            
            current_period = forecast_data.get('periods', [])[0] if forecast_data.get('periods') else {}
            
            # Parse precipitation type from forecast text
            precip_type = self._parse_precipitation_type(current_period)
            
            # Calculate black ice risk
            black_ice_risk = self._calculate_black_ice_risk(
                precip_type,
                current_period.get('temperature', 32)
            )
            
            return {
                'current_type': precip_type['type'],
                'intensity': precip_type['intensity'],
                'black_ice_risk': black_ice_risk,
                'forecast_next_hour': current_period.get('shortForecast', 'Unknown'),
                'temperature': current_period.get('temperature', None),
                'description': current_period.get('detailedForecast', ''),
                'wind_speed': current_period.get('windSpeed', 'Unknown'),
                'source': 'noaa_weather_gov'
            }
            
        except Exception as e:
            logger.error(f"Precipitation type detection error: {e}")
            return self._default_response()
    
    def _get_forecast(self, lat: float, lon: float) -> Optional[Dict]:
        """Get NOAA forecast data for location"""
        try:
            # First, get the forecast grid endpoint for this location
            points_url = f"{self.base_url}/points/{lat:.4f},{lon:.4f}"
            
            response = requests.get(points_url, timeout=30, headers={
                'User-Agent': 'QuantumBlackIceDetector/1.0'
            })
            
            if response.status_code != 200:
                logger.warning(f"NOAA points API error: {response.status_code}")
                return None
            
            points_data = response.json()
            
            # Get hourly forecast URL
            forecast_hourly_url = points_data.get('properties', {}).get('forecastHourly')
            
            if not forecast_hourly_url:
                logger.warning("No hourly forecast URL in NOAA response")
                return None
            
            # Get hourly forecast
            forecast_response = requests.get(forecast_hourly_url, timeout=30, headers={
                'User-Agent': 'QuantumBlackIceDetector/1.0'
            })
            
            if forecast_response.status_code != 200:
                logger.warning(f"NOAA forecast API error: {forecast_response.status_code}")
                return None
            
            forecast_data = forecast_response.json()
            return forecast_data.get('properties', {})
            
        except Exception as e:
            logger.error(f"NOAA forecast fetch error: {e}")
            return None
    
    def _parse_precipitation_type(self, period_data: Dict) -> Dict:
        """
        Parse precipitation type from NOAA forecast text
        
        NOAA doesn't always provide structured precip type, so we parse from text
        """
        forecast_text = (
            period_data.get('shortForecast', '') + ' ' + 
            period_data.get('detailedForecast', '')
        ).lower()
        
        # Detect freezing rain (HIGHEST BLACK ICE RISK)
        if any(keyword in forecast_text for keyword in ['freezing rain', 'freezing drizzle', 'ice pellets']):
            return {'type': 'freezing_rain', 'intensity': self._get_intensity(forecast_text)}
        
        # Detect sleet (HIGH BLACK ICE RISK)
        if 'sleet' in forecast_text:
            return {'type': 'sleet', 'intensity': self._get_intensity(forecast_text)}
        
        # Detect snow (MODERATE BLACK ICE RISK when melting)
        if any(keyword in forecast_text for keyword in ['snow', 'flurries', 'snow showers']):
            return {'type': 'snow', 'intensity': self._get_intensity(forecast_text)}
        
        # Detect regular rain (LOW-MODERATE BLACK ICE RISK if temp near freezing)
        if any(keyword in forecast_text for keyword in ['rain', 'showers', 'drizzle']):
            return {'type': 'rain', 'intensity': self._get_intensity(forecast_text)}
        
        # No precipitation
        return {'type': 'none', 'intensity': 'none'}
    
    def _get_intensity(self, forecast_text: str) -> str:
        """Determine precipitation intensity from forecast text"""
        if any(word in forecast_text for word in ['heavy', 'significant', 'major']):
            return 'heavy'
        elif any(word in forecast_text for word in ['light', 'slight', 'chance']):
            return 'light'
        else:
            return 'moderate'
    
    def _calculate_black_ice_risk(self, precip_type: Dict, temp: float) -> str:
        """
        Calculate black ice risk based on precipitation type and temperature
        
        Risk Levels:
        - CRITICAL: Freezing rain at any temp, or rain/snow when temp 28-34°F
        - HIGH: Sleet, or rain when temp 30-35°F
        - MODERATE: Snow when temp 25-32°F, or recent rain with temp dropping
        - LOW: No precipitation or temp well above freezing
        """
        ptype = precip_type['type']
        intensity = precip_type['intensity']
        
        # Freezing rain = CRITICAL (instant black ice)
        if ptype == 'freezing_rain':
            return 'critical'
        
        # Sleet = HIGH (accumulates and freezes)
        if ptype == 'sleet':
            return 'high' if intensity in ['moderate', 'heavy'] else 'moderate'
        
        # Rain near freezing = CRITICAL to HIGH
        if ptype == 'rain':
            if 28 <= temp <= 34:
                return 'critical'
            elif 30 <= temp <= 36:
                return 'high'
            elif 32 <= temp <= 38:
                return 'moderate'
            else:
                return 'low'
        
        # Snow = MODERATE (can melt and refreeze)
        if ptype == 'snow':
            if 28 <= temp <= 35:
                return 'moderate'
            else:
                return 'low'
        
        # No precipitation
        return 'low'
    
    def _default_response(self) -> Dict:
        """Return default response when API fails"""
        return {
            'current_type': 'unknown',
            'intensity': 'unknown',
            'black_ice_risk': 'moderate',
            'forecast_next_hour': 'Unable to determine',
            'temperature': None,
            'description': 'Precipitation data unavailable',
            'wind_speed': 'Unknown',
            'source': 'fallback'
        }
    
    def get_hourly_precipitation_forecast(self, lat: float, lon: float, hours: int = 6) -> list:
        """
        Get hour-by-hour precipitation forecast
        
        Returns list of hourly forecasts with precip type and black ice risk
        """
        try:
            forecast_data = self._get_forecast(lat, lon)
            
            if not forecast_data:
                return []
            
            periods = forecast_data.get('periods', [])[:hours]
            
            hourly_forecast = []
            for period in periods:
                precip_type = self._parse_precipitation_type(period)
                temp = period.get('temperature', 32)
                
                hourly_forecast.append({
                    'time': period.get('startTime'),
                    'hour_name': period.get('name'),
                    'temperature': temp,
                    'precipitation_type': precip_type['type'],
                    'intensity': precip_type['intensity'],
                    'black_ice_risk': self._calculate_black_ice_risk(precip_type, temp),
                    'short_forecast': period.get('shortForecast'),
                    'wind_speed': period.get('windSpeed')
                })
            
            return hourly_forecast
            
        except Exception as e:
            logger.error(f"Hourly forecast error: {e}")
            return []
