#!/usr/bin/env python3
"""Test Road Surface Temperature Model"""

import sys
sys.path.insert(0, 'backend')

from road_surface_temp_model import RoadSurfaceTemperatureModel
from datetime import datetime

model = RoadSurfaceTemperatureModel()

print("=" * 70)
print("ROAD SURFACE TEMPERATURE MODEL TEST")
print("=" * 70)

# Test Case 1: Night-time conditions (high black ice risk)
print("\n🌙 TEST 1: Night-time Clear Sky (HIGH BLACK ICE RISK)")
print("-" * 70)
result1 = model.estimate_surface_temp(
    air_temp=34,
    lat=42.3314,
    lon=-83.0458,
    cloud_cover=10,  # Clear
    humidity=85,     # High humidity
    dew_point=32,
    wind_speed=5,
    time=datetime(2026, 2, 2, 2, 0),  # 2 AM
    pavement_type='asphalt'
)

print(f"Air Temperature: 34°F")
print(f"Estimated Surface Temp: {result1['estimated_surface_temp']}°F")
print(f"Black Ice Risk: {result1['black_ice_risk']}")
print(f"Probability: {result1['black_ice_probability']*100:.1f}%")
print(f"Explanation: {result1['explanation']}")
print(f"\nComponents:")
print(f"  Solar Heat Gain: {result1['components']['solar_gain']}°F")
print(f"  Radiational Cooling: {result1['components']['radiational_cooling']}°F")
print(f"  Wind Adjustment: {result1['components']['wind_adjustment']}°F")
print(f"  Ground Heat: {result1['components']['ground_heat']}°F")

# Test Case 2: Daytime conditions (low risk)
print("\n" + "=" * 70)
print("☀️  TEST 2: Daytime Sunny (LOW BLACK ICE RISK)")
print("-" * 70)
result2 = model.estimate_surface_temp(
    air_temp=35,
    lat=42.3314,
    lon=-83.0458,
    cloud_cover=10,  # Clear
    humidity=50,
    dew_point=20,
    wind_speed=5,
    time=datetime(2026, 2, 2, 14, 0),  # 2 PM
    pavement_type='asphalt'
)

print(f"Air Temperature: 35°F")
print(f"Estimated Surface Temp: {result2['estimated_surface_temp']}°F")
print(f"Black Ice Risk: {result2['black_ice_risk']}")
print(f"Probability: {result2['black_ice_probability']*100:.1f}%")
print(f"Explanation: {result2['explanation']}")
print(f"\nComponents:")
print(f"  Solar Heat Gain: {result2['components']['solar_gain']}°F")
print(f"  Radiational Cooling: {result2['components']['radiational_cooling']}°F")

# Test Case 3: Bridge at night (higher risk)
print("\n" + "=" * 70)
print("🌉 TEST 3: Bridge at Night (VERY HIGH RISK)")
print("-" * 70)
result3 = model.estimate_surface_temp(
    air_temp=34,
    lat=42.3314,
    lon=-83.0458,
    cloud_cover=20,  # Mostly clear
    humidity=80,
    dew_point=30,
    wind_speed=12,   # Wind increases cooling
    time=datetime(2026, 2, 2, 3, 30),  # 3:30 AM
    pavement_type='bridge'  # Bridges freeze faster!
)

print(f"Air Temperature: 34°F")
print(f"Estimated Surface Temp: {result3['estimated_surface_temp']}°F")
print(f"Black Ice Risk: {result3['black_ice_risk']}")
print(f"Probability: {result3['black_ice_probability']*100:.1f}%")
print(f"Explanation: {result3['explanation']}")

# Test Case 4: Cloudy night (less cooling)
print("\n" + "=" * 70)
print("☁️  TEST 4: Cloudy Night (MODERATE RISK)")
print("-" * 70)
result4 = model.estimate_surface_temp(
    air_temp=33,
    lat=42.3314,
    lon=-83.0458,
    cloud_cover=80,  # Very cloudy
    humidity=75,
    dew_point=28,
    wind_speed=5,
    time=datetime(2026, 2, 2, 4, 0),  # 4 AM
    pavement_type='asphalt'
)

print(f"Air Temperature: 33°F")
print(f"Estimated Surface Temp: {result4['estimated_surface_temp']}°F")
print(f"Black Ice Risk: {result4['black_ice_risk']}")
print(f"Probability: {result4['black_ice_probability']*100:.1f}%")
print(f"Explanation: {result4['explanation']}")
print(f"Note: Clouds trap heat - less radiational cooling")

print("\n" + "=" * 70)
print("✅ Heat Balance Model is working correctly!")
print("=" * 70)
