"""
Heat Balance Model for Road Surface Temperature Estimation
Estimates pavement temperature when RWIS sensors unavailable
Uses solar radiation, radiational cooling, wind, and cloud cover
"""

import numpy as np
import logging
from datetime import datetime
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class RoadSurfaceTemperatureModel:
    """
    Estimates Road Surface Temperature (RST) without sensors
    
    Physics-based approach:
    RST = Air_Temp + Solar_Heat_Gain - Radiational_Cooling + Wind_Adjustment
    
    Critical for night-time black ice prediction
    """
    
    def __init__(self):
        self.pavement_thermal_mass = 0.8  # Asphalt absorbs/releases heat
        self.emissivity = 0.95  # Asphalt emissivity (0-1)
        self.albedo = 0.1  # Asphalt reflectivity (10% reflects sun)
        
        logger.info("Road Surface Temperature Model initialized")
    
    def estimate_surface_temp(self, 
                             air_temp: float,
                             lat: float,
                             lon: float,
                             cloud_cover: float = 50,
                             humidity: float = 70,
                             dew_point: float = None,
                             wind_speed: float = 5,
                             time: datetime = None,
                             pavement_type: str = 'asphalt') -> Dict:
        """
        Estimate road surface temperature using heat balance
        
        Args:
            air_temp: Air temperature (°F)
            lat: Latitude for solar calculations
            lon: Longitude for solar calculations
            cloud_cover: Cloud cover (0-100%)
            humidity: Relative humidity (%)
            dew_point: Dew point temperature (°F) [optional]
            wind_speed: Wind speed (mph)
            time: Datetime (defaults to now)
            pavement_type: 'asphalt', 'concrete', 'bridge', 'shaded'
            
        Returns:
            Dict with estimated surface temp, components, and black ice risk
        """
        if time is None:
            time = datetime.now()
        
        # Pavement properties by type
        properties = self._get_pavement_properties(pavement_type)
        
        # Component 1: Solar Radiation Heat Gain
        solar_heat = self._calculate_solar_heat_gain(
            lat, lon, time, cloud_cover, properties
        )
        
        # Component 2: Radiational Cooling (mainly at night)
        radiational_cooling = self._calculate_radiational_cooling(
            air_temp, dew_point or air_temp, time, cloud_cover, humidity, properties
        )
        
        # Component 3: Wind Adjustment
        wind_adjustment = self._calculate_wind_adjustment(
            wind_speed, air_temp, properties
        )
        
        # Component 4: Ground Heat Exchange
        ground_heat = self._calculate_ground_heat_exchange(time, properties)
        
        # Combined estimate
        surface_temp = (
            air_temp + 
            solar_heat - 
            radiational_cooling + 
            wind_adjustment + 
            ground_heat
        )
        
        # Adjust for thermal mass of pavement (temperature lag)
        surface_temp = self._apply_thermal_mass_lag(surface_temp, air_temp, properties)
        
        # Assess black ice risk
        black_ice_risk = self._assess_black_ice_risk(
            surface_temp, air_temp, humidity, dew_point or air_temp
        )
        
        return {
            'estimated_surface_temp': round(surface_temp, 1),
            'air_temp': air_temp,
            'components': {
                'solar_gain': round(solar_heat, 1),
                'radiational_cooling': round(radiational_cooling, 1),
                'wind_adjustment': round(wind_adjustment, 2),
                'ground_heat': round(ground_heat, 1)
            },
            'black_ice_risk': black_ice_risk['risk_level'],
            'black_ice_probability': round(black_ice_risk['probability'], 3),
            'dew_point_spread': round(surface_temp - (dew_point or air_temp), 1),
            'explanation': black_ice_risk['explanation'],
            'pavement_type': pavement_type,
            'hour': time.hour,
            'is_night': 19 <= time.hour or time.hour <= 6,
            'confidence': 'HIGH' if cloud_cover < 50 else 'MODERATE' if cloud_cover < 80 else 'LOW'
        }
    
    def _calculate_solar_heat_gain(self, 
                                   lat: float, 
                                   lon: float,
                                   time: datetime,
                                   cloud_cover: float,
                                   properties: Dict) -> float:
        """
        Calculate solar radiation heat gain on road surface
        
        During day: roads absorb solar energy
        At night: no solar gain
        """
        # Solar intensity at surface (W/m²)
        solar_constant = 1361  # W/m² at top of atmosphere
        
        # Solar zenith angle (simplified)
        hour = time.hour
        day_of_year = time.timetuple().tm_yday
        
        # Rough solar elevation angle calculation
        hour_angle = (hour - 12) * 15  # degrees
        declination = 23.44 * np.sin(np.radians((day_of_year - 81) * 360 / 365))
        lat_rad = np.radians(lat)
        
        sin_elevation = (
            np.sin(lat_rad) * np.sin(np.radians(declination)) +
            np.cos(lat_rad) * np.cos(np.radians(declination)) * 
            np.cos(np.radians(hour_angle))
        )
        
        # If sun below horizon, no solar gain
        if sin_elevation <= 0:
            return 0.0
        
        # Atmospheric transmission (reduced by clouds)
        cloud_factor = 1.0 - (cloud_cover / 100.0) * 0.75  # Clouds block 75% max
        
        # Solar radiation at surface
        direct_normal = solar_constant * 0.76  # After atmosphere
        direct_on_surface = direct_normal * sin_elevation
        
        # Diffuse radiation (from clouds)
        diffuse = solar_constant * 0.2 * sin_elevation * cloud_factor
        
        total_solar = (direct_on_surface + diffuse) * cloud_factor
        
        # Absorption (1 - albedo)
        absorbed = total_solar * (1 - properties['albedo'])
        
        # Convert to temperature increase (rough approximation)
        # ~500 W/m² = ~10°F increase for asphalt
        temp_gain = (absorbed / 500.0) * 10.0
        
        return max(0, temp_gain)
    
    def _calculate_radiational_cooling(self,
                                      air_temp: float,
                                      dew_point: float,
                                      time: datetime,
                                      cloud_cover: float,
                                      humidity: float,
                                      properties: Dict) -> float:
        """
        Calculate radiational cooling of road surface
        
        Clear nights: roads radiate heat and cool below air temp
        Cloudy nights: clouds trap heat, less cooling
        
        Stefan-Boltzmann Law with atmospheric factor
        """
        hour = time.hour
        
        # Nighttime check (roughly 18:00 to 06:00)
        is_night = hour >= 18 or hour <= 6
        
        if not is_night:
            return 0.0  # No radiational cooling during day
        
        # Stefan-Boltzmann radiational cooling
        # Q = ε * σ * (Ts^4 - Ta^4)
        stefan_boltzmann = 5.67e-8  # W/m²K⁴
        
        # Convert to Kelvin for calculation
        air_temp_k = (air_temp + 459.67) * 5/9
        
        # Assume surface ~2-5°F cooler than air initially
        surface_temp_k = ((air_temp - 3) + 459.67) * 5/9
        
        # Radiative heat loss (W/m²)
        radiation = (
            properties['emissivity'] * stefan_boltzmann * 
            (surface_temp_k**4 - air_temp_k**4)
        )
        
        # Atmospheric counter-radiation (trapped by clouds and humidity)
        # Clear dry night: full cooling | Cloudy humid night: reduced cooling
        cloud_factor = 1.0 - (cloud_cover / 100.0) * 0.8
        humidity_factor = 1.0 - (humidity / 100.0) * 0.3
        atmosphere_factor = cloud_factor * humidity_factor
        
        net_cooling = radiation * atmosphere_factor
        
        # Convert to temperature drop (°F per meter²)
        # Rough: ~100 W/m² = ~3°F cooling
        temp_drop = abs(net_cooling) / 100.0 * 3.0
        
        return max(0, temp_drop)
    
    def _calculate_wind_adjustment(self,
                                  wind_speed: float,
                                  air_temp: float,
                                  properties: Dict) -> float:
        """
        Adjust for wind effects on surface temperature
        
        High wind: evaporative cooling, faster temperature equilibration
        Low wind: surface can vary more from air temp
        """
        # Wind chill makes roads lose heat faster
        # But also reduces extreme temperature differences
        
        if wind_speed <= 2:
            # Very calm - more temperature variation possible
            return 0.0
        elif wind_speed <= 10:
            # Light wind - slight cooling effect
            return -0.3
        elif wind_speed <= 20:
            # Moderate wind - more evaporative cooling
            return -0.8
        else:
            # High wind - strong evaporative cooling
            return -1.2
    
    def _calculate_ground_heat_exchange(self,
                                       time: datetime,
                                       properties: Dict) -> float:
        """
        Heat exchange between road and ground below
        
        At night: ground releases stored heat to road (warming effect)
        In morning: ground absorbs heat from road (cooling effect)
        """
        hour = time.hour
        
        # Heat release from ground (mainly late night/early morning)
        if 22 <= hour or hour <= 4:
            # Ground slowly releases daytime heat
            return 0.5  # Modest warming from ground
        elif 4 < hour <= 6:
            # Early morning: transition to daytime heating
            return 0.2
        elif 6 < hour <= 16:
            # Day: no net heat release
            return 0.0
        else:
            # Late afternoon: no net exchange
            return 0.0
    
    def _apply_thermal_mass_lag(self,
                               estimated_temp: float,
                               air_temp: float,
                               properties: Dict) -> float:
        """
        Apply thermal mass lag - roads don't instantly match air temp
        
        Asphalt has significant thermal mass - temperature changes lag by 1-2 hours
        """
        # Thermal mass factor (0-1)
        # Higher = more lag, temperature stays closer to previous state
        lag_factor = properties['thermal_mass']
        
        # Road temperature lags behind changes
        # This smooths out rapid air temperature fluctuations
        lagged_temp = estimated_temp * 0.7 + air_temp * 0.3 * lag_factor
        
        return lagged_temp
    
    def _assess_black_ice_risk(self,
                              surface_temp: float,
                              air_temp: float,
                              humidity: float,
                              dew_point: float) -> Dict:
        """
        Assess black ice risk based on surface temperature and conditions
        """
        risk_level = "MINIMAL"
        probability = 0.0
        explanation = []
        
        # Primary condition: surface below freezing
        if surface_temp >= 32:
            probability = 0.0
            risk_level = "MINIMAL"
            explanation.append("Surface above freezing - no ice risk")
            return {
                'risk_level': risk_level,
                'probability': probability,
                'explanation': " ".join(explanation)
            }
        
        # Secondary condition: moisture present (humidity or dew point below surface)
        dew_point_spread = surface_temp - dew_point
        
        if dew_point_spread > 5:
            # Surface well above dew point - no condensation
            probability = 0.1
            explanation.append(f"Surface cold ({surface_temp:.0f}°F) but dry (dew point {dew_point:.0f}°F)")
            risk_level = "LOW"
        elif dew_point_spread > 0:
            # Close to dew point - possible condensation
            probability = 0.4
            explanation.append(f"Surface cold ({surface_temp:.0f}°F) and humid (dew point {dew_point:.0f}°F)")
            risk_level = "MODERATE"
        else:
            # Surface below dew point - condensation/moisture likely
            probability = 0.8
            explanation.append(f"Surface FREEZING ({surface_temp:.0f}°F) + moisture present")
            risk_level = "HIGH"
        
        # Amplify if very cold
        if surface_temp < 20:
            probability = min(1.0, probability * 1.3)
            explanation.append("Extreme cold - ice formation likely")
        
        # Reduce if warming trend
        if air_temp > surface_temp + 5:
            probability *= 0.8
            explanation.append("Air warming - conditions improving")
        
        return {
            'risk_level': risk_level,
            'probability': probability,
            'explanation': " | ".join(explanation)
        }
    
    def _get_pavement_properties(self, pavement_type: str) -> Dict:
        """Get thermal properties for different pavement types"""
        properties = {
            'asphalt': {
                'albedo': 0.10,  # Dark, absorbs heat
                'emissivity': 0.95,
                'thermal_mass': 0.8,
                'specific_heat': 920  # J/kg·K
            },
            'concrete': {
                'albedo': 0.35,  # Lighter than asphalt
                'emissivity': 0.92,
                'thermal_mass': 0.85,
                'specific_heat': 880
            },
            'bridge': {
                'albedo': 0.12,  # Similar to asphalt
                'emissivity': 0.95,
                'thermal_mass': 0.5,  # Less thermal mass - freezes faster!
                'specific_heat': 900
            },
            'shaded': {
                'albedo': 0.12,
                'emissivity': 0.95,
                'thermal_mass': 0.6,  # Less solar gain due to shade
                'specific_heat': 920
            }
        }
        
        return properties.get(pavement_type, properties['asphalt'])
    
    def forecast_surface_temp_12h(self,
                                  hourly_forecast: list,
                                  lat: float,
                                  lon: float,
                                  pavement_type: str = 'asphalt') -> list:
        """
        Forecast road surface temperature for next 12 hours
        
        Args:
            hourly_forecast: List of hourly weather forecasts
            lat, lon: Location coordinates
            pavement_type: Type of pavement
            
        Returns:
            List of surface temp estimates with black ice risk
        """
        forecast = []
        base_time = datetime.now()
        
        for i, hour_data in enumerate(hourly_forecast[:12]):
            timestamp = base_time.replace(hour=(base_time.hour + i) % 24)
            
            result = self.estimate_surface_temp(
                air_temp=hour_data.get('temperature', 32),
                lat=lat,
                lon=lon,
                cloud_cover=hour_data.get('clouds', 50),
                humidity=hour_data.get('humidity', 70),
                dew_point=hour_data.get('dew_point', 28),
                wind_speed=hour_data.get('wind_speed', 5),
                time=timestamp,
                pavement_type=pavement_type
            )
            
            forecast.append({
                'hour': i,
                'timestamp': timestamp.isoformat(),
                'surface_temp': result['estimated_surface_temp'],
                'air_temp': result['air_temp'],
                'black_ice_risk': result['black_ice_risk'],
                'probability': result['black_ice_probability'],
                'is_night': result['is_night']
            })
        
        return forecast
