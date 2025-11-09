"""
Enhanced Bridge Freeze Calculator
Bridges freeze at WARMER temperatures than regular roads due to:
1. Air circulation below bridge (cools from both top and bottom)
2. No ground heat from below
3. Metal/concrete structure conducts heat away faster

Rule: Bridges can freeze when air temp is 35-40°F (5-10°F warmer than road freeze point)
"""

import logging
from typing import Dict, Optional
import math

logger = logging.getLogger(__name__)

class BridgeFreezeCalculator:
    """Calculate freeze risk specifically for bridges and overpasses"""
    
    def __init__(self):
        logger.info("Bridge Freeze Calculator initialized")
    
    def calculate_bridge_freeze_temp(
        self, 
        air_temp_f: float,
        wind_speed_mph: float,
        humidity_percent: float,
        bridge_material: str = 'concrete',
        bridge_length_ft: Optional[float] = None
    ) -> Dict:
        """
        Calculate when a bridge will freeze
        
        Args:
            air_temp_f: Air temperature in Fahrenheit
            wind_speed_mph: Wind speed (affects wind chill on bridge surface)
            humidity_percent: Relative humidity
            bridge_material: 'concrete', 'steel', or 'composite'
            bridge_length_ft: Bridge length (longer = more exposed)
            
        Returns:
            {
                'bridge_freeze_temp_f': float,  # Temp at which bridge surface freezes
                'regular_road_freeze_temp_f': float,  # Temp for regular road
                'temp_difference': float,  # How much warmer bridge freezes
                'freeze_risk': 'critical' | 'high' | 'moderate' | 'low',
                'warning_message': str,
                'time_to_freeze_minutes': int or None
            }
        """
        
        # Base freeze temperature for regular road (with ground heat)
        regular_road_freeze = 32.0
        
        # Bridge freezes warmer due to air circulation
        # Formula: Bridges freeze when air temp is 5-10°F above 32°F
        base_bridge_offset = 8.0  # Bridges freeze at ~40°F air temp
        
        # Adjust for wind (more wind = faster heat loss = freezes at warmer temp)
        wind_offset = self._calculate_wind_offset(wind_speed_mph)
        
        # Adjust for humidity (high humidity = frost forms easier)
        humidity_offset = self._calculate_humidity_offset(humidity_percent)
        
        # Adjust for bridge material
        material_offset = self._get_material_offset(bridge_material)
        
        # Adjust for bridge length (longer = more exposed)
        length_offset = self._calculate_length_offset(bridge_length_ft) if bridge_length_ft else 0
        
        # Total bridge freeze offset
        total_offset = base_bridge_offset + wind_offset + humidity_offset + material_offset + length_offset
        
        # Bridge freeze temperature
        bridge_freeze_temp = regular_road_freeze + total_offset
        
        # Calculate current freeze risk
        freeze_risk, warning = self._calculate_freeze_risk(air_temp_f, bridge_freeze_temp)
        
        # Estimate time to freeze (if currently above freeze temp)
        time_to_freeze = self._estimate_freeze_time(
            air_temp_f, 
            bridge_freeze_temp,
            wind_speed_mph
        )
        
        return {
            'bridge_freeze_temp_f': round(bridge_freeze_temp, 1),
            'regular_road_freeze_temp_f': regular_road_freeze,
            'temp_difference': round(total_offset, 1),
            'current_air_temp_f': air_temp_f,
            'freeze_risk': freeze_risk,
            'warning_message': warning,
            'time_to_freeze_minutes': time_to_freeze,
            'factors': {
                'wind_offset': round(wind_offset, 1),
                'humidity_offset': round(humidity_offset, 1),
                'material_offset': round(material_offset, 1),
                'length_offset': round(length_offset, 1) if bridge_length_ft else 0
            }
        }
    
    def _calculate_wind_offset(self, wind_speed_mph: float) -> float:
        """
        More wind = bridge freezes at even warmer temperature
        Wind accelerates heat loss from bridge surface
        """
        if wind_speed_mph > 20:
            return 3.0  # High wind: freezes at +3°F warmer
        elif wind_speed_mph > 10:
            return 2.0  # Moderate wind: +2°F
        elif wind_speed_mph > 5:
            return 1.0  # Light wind: +1°F
        else:
            return 0.0  # Calm: no additional offset
    
    def _calculate_humidity_offset(self, humidity_percent: float) -> float:
        """
        Higher humidity = frost/ice forms easier on bridge
        """
        if humidity_percent > 80:
            return 2.0  # High humidity: +2°F offset
        elif humidity_percent > 60:
            return 1.0  # Moderate: +1°F
        else:
            return 0.0  # Low: no offset
    
    def _get_material_offset(self, material: str) -> float:
        """
        Different materials have different freeze characteristics
        """
        material_map = {
            'steel': 3.0,      # Steel conducts heat away fastest
            'metal': 3.0,
            'concrete': 1.5,   # Concrete is middle
            'composite': 1.0,  # Composite materials slightly better
            'wood': 0.5        # Wood (old bridges) retains heat better
        }
        return material_map.get(material.lower(), 1.5)  # Default to concrete
    
    def _calculate_length_offset(self, length_ft: float) -> float:
        """
        Longer bridges = more exposed to wind and air circulation
        """
        if length_ft > 1000:
            return 1.5  # Very long bridge (1000+ ft)
        elif length_ft > 500:
            return 1.0  # Long bridge (500-1000 ft)
        elif length_ft > 200:
            return 0.5  # Medium bridge
        else:
            return 0.0  # Short bridge/overpass
    
    def _calculate_freeze_risk(self, current_temp_f: float, freeze_temp_f: float) -> tuple:
        """
        Determine freeze risk level based on how close current temp is to freeze temp
        """
        temp_margin = current_temp_f - freeze_temp_f
        
        if temp_margin <= 0:
            # Already at or below freeze temp
            return (
                'critical',
                f'⚠️ BRIDGE FREEZING NOW! Surface temp at or below {freeze_temp_f}°F'
            )
        elif temp_margin <= 2:
            # Within 2°F of freezing
            return (
                'critical',
                f'🚨 CRITICAL: Bridge will freeze in minutes! Only {temp_margin:.1f}°F from freeze point'
            )
        elif temp_margin <= 5:
            # Within 5°F
            return (
                'high',
                f'🔴 HIGH RISK: Bridge may freeze soon. {temp_margin:.1f}°F above freeze point ({freeze_temp_f}°F)'
            )
        elif temp_margin <= 10:
            # Within 10°F
            return (
                'moderate',
                f'🟡 MODERATE: Monitor bridge conditions. {temp_margin:.1f}°F above freeze point'
            )
        else:
            # More than 10°F above
            return (
                'low',
                f'✅ LOW RISK: Bridge unlikely to freeze. {temp_margin:.1f}°F above freeze point'
            )
    
    def _estimate_freeze_time(
        self, 
        current_temp_f: float, 
        freeze_temp_f: float,
        wind_speed_mph: float
    ) -> Optional[int]:
        """
        Estimate minutes until bridge freezes (rough approximation)
        
        Assumptions:
        - Bridge surface cools ~1°F per 5-10 minutes depending on wind
        - This is a ROUGH estimate for user awareness
        """
        temp_drop_needed = current_temp_f - freeze_temp_f
        
        if temp_drop_needed <= 0:
            return 0  # Already freezing
        
        # Cooling rate depends on wind
        if wind_speed_mph > 15:
            minutes_per_degree = 3  # Fast cooling with high wind
        elif wind_speed_mph > 7:
            minutes_per_degree = 5  # Moderate cooling
        else:
            minutes_per_degree = 8  # Slow cooling with light wind
        
        estimated_minutes = int(temp_drop_needed * minutes_per_degree)
        
        # Cap at 180 minutes (3 hours) for realism
        return min(estimated_minutes, 180)
    
    def compare_bridge_vs_road(
        self,
        air_temp_f: float,
        wind_speed_mph: float,
        humidity_percent: float,
        bridge_material: str = 'concrete'
    ) -> Dict:
        """
        Direct comparison: When will bridge freeze vs when will regular road freeze
        
        Returns detailed comparison showing the danger window where
        bridges are icy but regular roads are still safe
        """
        bridge_calc = self.calculate_bridge_freeze_temp(
            air_temp_f, wind_speed_mph, humidity_percent, bridge_material
        )
        
        regular_road_freeze = 32.0
        bridge_freeze = bridge_calc['bridge_freeze_temp_f']
        
        # The "danger zone" where bridges are frozen but roads are not
        danger_zone = (
            air_temp_f >= regular_road_freeze and 
            air_temp_f <= bridge_freeze
        )
        
        return {
            'bridge_freeze_temp': bridge_freeze,
            'road_freeze_temp': regular_road_freeze,
            'current_air_temp': air_temp_f,
            'in_danger_zone': danger_zone,
            'bridge_frozen': air_temp_f <= bridge_freeze,
            'road_frozen': air_temp_f <= regular_road_freeze,
            'warning': self._get_comparison_warning(
                air_temp_f, bridge_freeze, regular_road_freeze, danger_zone
            ),
            'bridge_details': bridge_calc
        }
    
    def _get_comparison_warning(
        self,
        air_temp: float,
        bridge_freeze: float,
        road_freeze: float,
        in_danger_zone: bool
    ) -> str:
        """Generate warning message for bridge vs road comparison"""
        if in_danger_zone:
            return (
                f"⚠️ BRIDGE DANGER ZONE! Air temp {air_temp}°F is warm enough for roads "
                f"({road_freeze}°F freeze point) but COLD ENOUGH FOR BRIDGES "
                f"({bridge_freeze}°F freeze point). BRIDGES MAY BE ICY WHILE ROADS ARE CLEAR!"
            )
        elif air_temp <= road_freeze:
            return (
                f"🚨 BOTH BRIDGES AND ROADS FROZEN! Air temp {air_temp}°F is below "
                f"freeze point for all surfaces. EXTREME CAUTION!"
            )
        else:
            return (
                f"✅ Both bridges and roads safe. Air temp {air_temp}°F is above "
                f"bridge freeze point ({bridge_freeze}°F)."
            )
