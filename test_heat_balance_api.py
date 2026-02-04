#!/usr/bin/env python3
"""
Test the /api/heat-balance endpoint with various scenarios
"""

import requests
import json

BASE_URL = "http://localhost:5000"

test_cases = [
    {
        "name": "Night Clear Sky (HIGH RISK)",
        "data": {
            "air_temp": 34,
            "wind_speed": 8,
            "cloud_cover": 10,  # Clear skies
            "is_daytime": False,
            "dew_point": 30
        }
    },
    {
        "name": "Daytime Sunny (MINIMAL RISK)",
        "data": {
            "air_temp": 35,
            "wind_speed": 5,
            "cloud_cover": 0,  # Clear
            "is_daytime": True,
            "dew_point": 25
        }
    },
    {
        "name": "Night Cloudy (MODERATE RISK)",
        "data": {
            "air_temp": 33,
            "wind_speed": 3,
            "cloud_cover": 80,  # Very cloudy
            "is_daytime": False,
            "dew_point": 28
        }
    },
    {
        "name": "Extreme Cold Night (EXTREME RISK)",
        "data": {
            "air_temp": 20,
            "wind_speed": 12,
            "cloud_cover": 5,
            "is_daytime": False,
            "dew_point": 10
        }
    },
    {
        "name": "Night with Wind (HIGH RISK)",
        "data": {
            "air_temp": 32,
            "wind_speed": 15,  # High wind
            "cloud_cover": 20,
            "is_daytime": False,
            "dew_point": 28
        }
    }
]

print("=" * 80)
print("HEAT BALANCE API TEST")
print("=" * 80)

for test in test_cases:
    print(f"\n📊 TEST: {test['name']}")
    print("-" * 80)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/heat-balance",
            json=test['data'],
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ SUCCESS")
            print(f"   Air Temp:          {result['air_temp']}°F")
            print(f"   Road Surface Temp: {result['estimated_road_temp']}°F")
            print(f"   Temperature Drop:  {result['air_temp'] - result['estimated_road_temp']:.1f}°F")
            print(f"   Risk Level:        {result['risk_level']} (color: {result['color_code']})")
            print(f"   Black Ice Prob:    {result['black_ice_probability']*100:.0f}%")
            print(f"   \n   Components:")
            print(f"     • Solar Gain:           {result['components']['solar_gain']:+.1f}°F")
            print(f"     • Radiational Cooling:  {result['components']['radiational_cooling']:+.1f}°F")
            print(f"     • Wind Effect:          {result['components']['wind_effect']:+.1f}°F")
            print(f"   \n   Explanation: {result['explanation']}")
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"   Response: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("❌ FAILED: Cannot connect to server")
        print("   Make sure Flask server is running on http://localhost:5000")
        break
    except Exception as e:
        print(f"❌ ERROR: {e}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
