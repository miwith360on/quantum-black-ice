"""
Bridge Freeze Calculator

Why bridges ice first: a bridge deck has cold air above AND below it and no
ground underneath to feed it heat. On clear, calm nights it radiates heat to
the sky and can end up several degrees colder than the air, so it can ice
over while the air (and regular roads) are still above 32°F.

How this model works:
  1. Estimate the deck surface temperature from air temperature, cloud cover,
     wind, time of day, material and length.
       - Clear skies + calm wind + night = most cooling (deck well below air).
       - Wind mixes the air and keeps the deck close to air temperature.
         It does NOT make the deck colder than the air.
       - Daytime sun warms the deck.
  2. Ice needs water. Check for moisture: frost when the deck is at or below
     the dew point, or a wet deck from recent precipitation / near-saturated air.
  3. Risk = deck temperature vs 32°F, combined with whether moisture is there.

All temperatures in °F, wind in mph.
"""

import logging
import math
from typing import Dict, Optional

logger = logging.getLogger(__name__)

FREEZING_F = 32.0
MAX_RADIATIVE_COOLING_F = 6.0   # deck below air on a clear, calm night
NO_GROUND_HEAT_F = 1.0          # bridges lack the ground heat that roads get

MATERIAL_OFFSET_F = {
    'steel': 1.0,      # thin steel decks lose heat fastest
    'metal': 1.0,
    'concrete': 0.0,
    'composite': 0.0,
    'wood': -0.5,
}


class BridgeFreezeCalculator:
    """Estimate ice risk on a bridge deck from current weather."""

    def __init__(self):
        logger.info("Bridge Freeze Calculator initialized")

    def calculate_bridge_freeze_temp(
        self,
        air_temp_f: float,
        wind_speed_mph: float,
        humidity_percent: float,
        bridge_material: str = 'concrete',
        bridge_length_ft: Optional[float] = None,
        dew_point_f: Optional[float] = None,
        cloud_cover_percent: Optional[float] = None,
        is_night: Optional[bool] = None,
        recent_precip: bool = False,
    ) -> Dict:
        air_temp_f = float(air_temp_f)
        wind_speed_mph = float(wind_speed_mph or 0)
        humidity_percent = float(humidity_percent if humidity_percent is not None else 70)
        material = (bridge_material or 'concrete').lower()

        if dew_point_f is None:
            dew_point_f = self._dew_point_f(air_temp_f, humidity_percent)

        # --- 1. How much colder than the air is the deck? ---
        sky = self._sky_factor(cloud_cover_percent)
        wind = self._wind_factor(wind_speed_mph)
        time_of_day = 0.7 if is_night is None else (1.0 if is_night else 0.3)
        radiative = MAX_RADIATIVE_COOLING_F * sky * wind * time_of_day

        material_offset = MATERIAL_OFFSET_F.get(material, 0.0)
        length_offset = 0.5 if (bridge_length_ft or 0) > 500 else 0.0

        total_offset = max(0.0, radiative + NO_GROUND_HEAT_F + material_offset + length_offset)
        deck_temp_f = air_temp_f - total_offset

        # Air temp at which this deck reaches 32°F ("watch zone" threshold)
        watch_zone_air_temp = FREEZING_F + total_offset

        # --- 2. Is there water to freeze? ---
        frost_possible = deck_temp_f <= dew_point_f + 1.0
        wet_deck = bool(recent_precip) or humidity_percent >= 92
        moisture = frost_possible or wet_deck

        # --- 3. Risk ---
        risk, warning = self._risk(deck_temp_f, moisture, frost_possible, wet_deck)

        minutes = None
        if risk != 'critical' and air_temp_f - watch_zone_air_temp <= 5:
            # Rough: decks cool ~1°F every 6-15 min at night depending on sky/wind
            minutes_per_degree = 6 if sky * wind > 0.6 else 10 if sky * wind > 0.3 else 15
            minutes = int(max(0, deck_temp_f - FREEZING_F) * minutes_per_degree)

        return {
            # Main outputs
            'freeze_risk': risk,
            'warning_message': warning,
            'estimated_deck_temp_f': round(deck_temp_f, 1),
            'current_air_temp_f': round(air_temp_f, 1),
            'dew_point_f': round(dew_point_f, 1),
            'bridge_freeze_temp_f': round(watch_zone_air_temp, 1),
            'regular_road_freeze_temp_f': FREEZING_F,
            'temp_difference': round(total_offset, 1),
            'moisture_present': moisture,
            'frost_possible': frost_possible,
            'wet_deck': wet_deck,
            'currently_frozen': risk == 'critical',
            'will_freeze_soon': risk == 'high',
            'time_to_freeze_minutes': minutes,
            'factors': {
                'sky_cooling_f': round(radiative, 1),
                'no_ground_heat_f': NO_GROUND_HEAT_F,
                'material_offset_f': material_offset,
                'length_offset_f': length_offset,
            },
            'inputs': {
                'material': material,
                'length_ft': bridge_length_ft,
                'wind_mph': round(wind_speed_mph, 1),
                'humidity': round(humidity_percent),
                'cloud_cover': cloud_cover_percent,
                'is_night': is_night,
            },
        }

    # ---------- helpers ----------

    @staticmethod
    def _sky_factor(cloud_cover: Optional[float]) -> float:
        if cloud_cover is None:
            return 0.5
        if cloud_cover < 30:
            return 1.0
        if cloud_cover < 70:
            return 0.5
        return 0.15  # overcast: clouds trap heat

    @staticmethod
    def _wind_factor(wind_mph: float) -> float:
        if wind_mph < 5:
            return 1.0
        if wind_mph < 10:
            return 0.6
        if wind_mph < 15:
            return 0.35
        return 0.2  # windy: deck stays near air temperature

    @staticmethod
    def _dew_point_f(temp_f: float, rh: float) -> float:
        t = (temp_f - 32) * 5 / 9
        rh = min(max(rh, 1.0), 100.0)
        a, b = 17.62, 243.12
        g = math.log(rh / 100.0) + a * t / (b + t)
        return (b * g / (a - g)) * 9 / 5 + 32

    @staticmethod
    def _risk(deck_exact: float, moisture: bool, frost: bool, wet: bool) -> tuple:
        deck = deck_exact
        shown = math.floor(deck_exact)  # round down so 31.6°F never displays as "32°F"
        if deck <= FREEZING_F and moisture:
            why = 'frost forming on the deck' if frost and not wet else 'moisture on the deck'
            return 'critical', f'🚨 Ice likely now: deck is about {shown}°F with {why}'
        if deck <= FREEZING_F:
            return 'high', f'🔴 Deck is about {shown}°F but dry. Any rain, snow or mist will freeze on contact'
        if deck <= 35 and moisture:
            return 'high', f'🔴 Deck is about {shown}°F and damp. Could ice up with a small temperature drop'
        if deck <= 35:
            return 'moderate', f'🟡 Deck is about {shown}°F. Close to freezing, but dry'
        if deck <= 38 and moisture:
            return 'moderate', f'🟡 Deck is about {shown}°F and damp. Watch it if temperatures keep falling'
        return 'low', f'✅ Deck is about {shown}°F. Ice unlikely right now'

    def compare_bridge_vs_road(self, air_temp_f, wind_speed_mph, humidity_percent,
                               bridge_material='concrete', **kwargs) -> Dict:
        """Compare bridge vs regular road at the same weather."""
        bridge = self.calculate_bridge_freeze_temp(
            air_temp_f, wind_speed_mph, humidity_percent, bridge_material, **kwargs)
        deck = bridge['estimated_deck_temp_f']
        # A road has ground heat and cools roughly half as much as a deck
        road = float(air_temp_f) - bridge['factors']['sky_cooling_f'] * 0.5
        danger_zone = deck <= FREEZING_F < road
        if danger_zone:
            warning = ('⚠️ Bridge danger zone: bridges may be icy while regular roads are still above freezing')
        elif road <= FREEZING_F:
            warning = '🚨 Bridges and roads are both at or below freezing'
        else:
            warning = '✅ Bridges and roads both above freezing'
        return {
            'bridge_deck_temp': deck,
            'road_surface_temp': round(road, 1),
            'current_air_temp': air_temp_f,
            'in_danger_zone': danger_zone,
            'bridge_frozen': deck <= FREEZING_F,
            'road_frozen': road <= FREEZING_F,
            'warning': warning,
            'bridge_details': bridge,
        }
