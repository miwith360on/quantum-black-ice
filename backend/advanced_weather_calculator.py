"""
Advanced Weather Calculations
Calculates dew point, wind chill, heat index, and other derived metrics
"""

import math
import logging

logger = logging.getLogger(__name__)

class AdvancedWeatherCalculator:
    """Calculate advanced weather metrics for enhanced black ice detection"""
    
    @staticmethod
    def calculate_dew_point(temp_f, humidity_percent):
        """
        Calculate dew point temperature using Magnus formula
        
        Args:
            temp_f: Temperature in Fahrenheit
            humidity_percent: Relative humidity (0-100)
        
        Returns:
            Dew point in Fahrenheit
        """
        # Convert to Celsius
        temp_c = (temp_f - 32) * 5/9
        humidity = humidity_percent / 100.0
        
        # Constants for Magnus formula
        a = 17.27
        b = 237.7
        
        # Calculate alpha
        alpha = ((a * temp_c) / (b + temp_c)) + math.log(humidity)
        
        # Calculate dew point in Celsius
        dew_point_c = (b * alpha) / (a - alpha)
        
        # Convert back to Fahrenheit
        dew_point_f = (dew_point_c * 9/5) + 32
        
        logger.debug(f"Dew point: {dew_point_f:.1f}°F (temp: {temp_f}°F, humidity: {humidity_percent}%)")
        
        return round(dew_point_f, 1)
    
    @staticmethod
    def calculate_wind_chill(temp_f, wind_mph):
        """
        Calculate wind chill temperature
        Only valid for temps <= 50°F and wind >= 3 mph
        
        Args:
            temp_f: Temperature in Fahrenheit
            wind_mph: Wind speed in mph
        
        Returns:
            Wind chill in Fahrenheit
        """
        # Handle None values
        if temp_f is None or wind_mph is None:
            return temp_f if temp_f is not None else 32
        
        if temp_f > 50 or wind_mph < 3:
            return temp_f
        
        # Wind chill formula
        wind_chill = (35.74 + 
                     (0.6215 * temp_f) - 
                     (35.75 * (wind_mph ** 0.16)) + 
                     (0.4275 * temp_f * (wind_mph ** 0.16)))
        
        return round(wind_chill, 1)
    
    @staticmethod
    def calculate_heat_index(temp_f, humidity_percent):
        """
        Calculate heat index (feels-like temperature in heat)
        Only valid for temps >= 80°F
        
        Args:
            temp_f: Temperature in Fahrenheit
            humidity_percent: Relative humidity (0-100)
        
        Returns:
            Heat index in Fahrenheit
        """
        # Handle None values
        if temp_f is None or humidity_percent is None:
            return temp_f if temp_f is not None else 32
        
        if temp_f < 80:
            return temp_f
        
        T = temp_f
        RH = humidity_percent
        
        # Rothfusz regression
        heat_index = (-42.379 + 
                     2.04901523 * T + 
                     10.14333127 * RH - 
                     0.22475541 * T * RH - 
                     0.00683783 * T * T - 
                     0.05481717 * RH * RH + 
                     0.00122874 * T * T * RH + 
                     0.00085282 * T * RH * RH - 
                     0.00000199 * T * T * RH * RH)
        
        return round(heat_index, 1)
    
    @staticmethod
    def calculate_feels_like(temp_f, humidity_percent, wind_mph):
        """
        Calculate feels-like temperature (combines wind chill and heat index)
        
        Args:
            temp_f: Temperature in Fahrenheit
            humidity_percent: Relative humidity (0-100)
            wind_mph: Wind speed in mph
        
        Returns:
            Feels-like temperature in Fahrenheit
        """
        # Handle None values
        if temp_f is None:
            return 32
        if humidity_percent is None:
            humidity_percent = 50
        if wind_mph is None:
            wind_mph = 0
        
        if temp_f <= 50 and wind_mph >= 3:
            return AdvancedWeatherCalculator.calculate_wind_chill(temp_f, wind_mph)
        elif temp_f >= 80:
            return AdvancedWeatherCalculator.calculate_heat_index(temp_f, humidity_percent)
        else:
            return temp_f
    
    @staticmethod
    def estimate_road_surface_temp(air_temp_f, cloud_cover_percent, wind_mph, hour):
        """
        Estimate road surface temperature
        Roads can be significantly colder than air temperature
        
        Args:
            air_temp_f: Air temperature in Fahrenheit
            cloud_cover_percent: Cloud cover (0-100)
            wind_mph: Wind speed in mph
            hour: Hour of day (0-23)
        
        Returns:
            Estimated road surface temperature in Fahrenheit
        """
        offset = 0
        
        # Base offset - roads radiate heat
        offset -= 2
        
        # Clear skies at night = more radiative cooling
        if hour < 6 or hour > 20:
            if cloud_cover_percent < 30:
                offset -= 5  # Clear night - significant cooling
            elif cloud_cover_percent < 60:
                offset -= 3  # Partly cloudy night
        
        # Daytime solar heating
        elif 10 <= hour <= 16:
            if cloud_cover_percent < 30:
                offset += 3  # Sunny - road heats up
            elif cloud_cover_percent < 60:
                offset += 1  # Partly sunny
        
        # Wind effect
        if wind_mph > 15:
            offset += 2  # Wind prevents extreme cooling
        elif wind_mph < 5:
            offset -= 1  # Calm air allows cooling
        
        road_temp = air_temp_f + offset
        
        logger.debug(f"Estimated road temp: {road_temp:.1f}°F (air: {air_temp_f}°F, offset: {offset}°F)")
        
        return round(road_temp, 1)
    
    @staticmethod
    def calculate_frost_point(temp_f, humidity_percent):
        """
        Calculate frost point (like dew point, but below freezing)
        
        Args:
            temp_f: Temperature in Fahrenheit
            humidity_percent: Relative humidity (0-100)
        
        Returns:
            Frost point in Fahrenheit
        """
        # Similar to dew point but uses ice saturation vapor pressure
        temp_c = (temp_f - 32) * 5/9
        humidity = humidity_percent / 100.0
        
        if temp_c >= 0:
            # Above freezing, use dew point
            return AdvancedWeatherCalculator.calculate_dew_point(temp_f, humidity_percent)
        
        # Below freezing, calculate frost point
        a = 22.46
        b = 272.62
        
        alpha = ((a * temp_c) / (b + temp_c)) + math.log(humidity)
        frost_point_c = (b * alpha) / (a - alpha)
        frost_point_f = (frost_point_c * 9/5) + 32
        
        return round(frost_point_f, 1)
    
    @staticmethod
    def is_black_ice_conditions(temp_f, dew_point_f, road_temp_f, precipitation):
        """
        Quick check if conditions are favorable for black ice
        
        Args:
            temp_f: Air temperature
            dew_point_f: Dew point temperature
            road_temp_f: Road surface temperature
            precipitation: Recent precipitation (True/False)
        
        Returns:
            Boolean indicating black ice risk
        """
        # Classic black ice conditions:
        # 1. Road temp at or below freezing
        # 2. Recent precipitation or high moisture
        # 3. Temperature near freezing point
        
        if road_temp_f <= 32 and 20 <= temp_f <= 40:
            if precipitation or (temp_f - dew_point_f) < 5:
                return True
        
        return False
    
    @staticmethod
    def enhance_weather_data(weather_data):
        """
        Add all calculated metrics to weather data
        
        Args:
            weather_data: Dictionary with basic weather data
        
        Returns:
            Enhanced weather data with calculated fields
        """
        # Get values with proper None handling and defaults
        temp = weather_data.get('temperature')
        if temp is None:
            temp = 32
        humidity = weather_data.get('humidity')
        if humidity is None:
            humidity = 50
        wind = weather_data.get('wind_speed')
        if wind is None:
            wind = 0
        clouds = weather_data.get('clouds')
        if clouds is None:
            clouds = 50
        hour = weather_data.get('hour', 12)
        
        # Calculate all metrics
        dew_point = AdvancedWeatherCalculator.calculate_dew_point(temp, humidity)
        feels_like = AdvancedWeatherCalculator.calculate_feels_like(temp, humidity, wind)
        wind_chill = AdvancedWeatherCalculator.calculate_wind_chill(temp, wind)
        road_temp = AdvancedWeatherCalculator.estimate_road_surface_temp(temp, clouds, wind, hour)
        frost_point = AdvancedWeatherCalculator.calculate_frost_point(temp, humidity)
        
        # Add to weather data
        weather_data['dew_point'] = dew_point
        weather_data['feels_like'] = feels_like
        weather_data['wind_chill'] = wind_chill
        weather_data['road_temperature'] = road_temp
        weather_data['frost_point'] = frost_point
        weather_data['dew_point_spread'] = temp - dew_point
        
        logger.info(f"Enhanced weather data: temp={temp}°F, dew={dew_point}°F, road={road_temp}°F")
        
        return weather_data
