"""
Test script for Hybrid BIFI v2 and Validation Dashboard
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from bifi_calculator_v2 import HybridBIFI
from feedback_system import feedback_system

print("="*60)
print("🧪 Testing Hybrid BIFI v2.0.0")
print("="*60)

# Initialize
bifi = HybridBIFI()

# Test scenarios
scenarios = [
    {
        "name": "High Risk - Cold, Wet Bridge",
        "data": {
            "temp": 30,
            "humidity": 85,
            "dew_point": 28,
            "wind_speed": 15,
            "precip_probability": 0.8,
            "road_temp": 28,
            "is_bridge": True,
            "cloud_cover": 20,
            "hour": 3
        }
    },
    {
        "name": "Low Risk - Warm Dry Day",
        "data": {
            "temp": 50,
            "humidity": 40,
            "dew_point": 30,
            "wind_speed": 5,
            "precip_probability": 0.0,
            "road_temp": 52,
            "is_bridge": False,
            "cloud_cover": 80,
            "hour": 14
        }
    },
    {
        "name": "Medium Risk - Borderline Temps",
        "data": {
            "temp": 34,
            "humidity": 70,
            "dew_point": 30,
            "wind_speed": 10,
            "precip_probability": 0.5,
            "road_temp": 32,
            "is_bridge": False,
            "cloud_cover": 50,
            "hour": 22
        }
    }
]

for scenario in scenarios:
    print(f"\n🔍 {scenario['name']}")
    print("-" * 60)
    
    result = bifi.calculate(scenario['data'])
    
    components = result['components']
    print(f"BIFI Score: {result['bifi_score']:.1f}%")
    print(f"Risk Level: {result['risk_level']} ({result['risk_color']})")
    print(f"\nComponents:")
    print(f"  P(wet): {components['p_wet']*100:.1f}%")
    print(f"  P(freeze): {components['p_freeze']*100:.1f}%")
    print(f"  Bridge multiplier: {components['bridge_multiplier']:.2f}x")
    print(f"  Uncertainty adjustment: {components['uncertainty_adjustment']:.2f}x")
    print(f"\nExplanation:")
    print(f"  {result['explanation']}")
    
    # Show wetness features
    print(f"\nWetness Features:")
    for feat, val in result['features']['wetness'].items():
        if isinstance(val, (int, float)):
            print(f"  • {feat}: {val:.2f}")
        else:
            print(f"  • {feat}: {val}")
    
    # Show freeze features
    print(f"\nFreeze Features:")
    for feat, val in result['features']['freeze'].items():
        if isinstance(val, (int, float)):
            print(f"  • {feat}: {val:.2f}")
        else:
            print(f"  • {feat}: {val}")

print("\n" + "="*60)
print("📊 Testing Feedback System")
print("="*60)

# Test feedback submission
test_report = {
    "lat": 40.7128,
    "lon": -74.0060,
    "actual_condition": "icy",
    "predicted_condition": "minimal",
    "predicted_probability": 0.15,
    "user_comment": "Test report for validation"
}

report = feedback_system.submit_report(**test_report)
print(f"\n✅ Created test report: ID {report['id']}")

# Get accuracy stats
stats = feedback_system.get_accuracy_stats()
print(f"\n📈 Accuracy Stats:")
print(f"  Total reports: {stats['total_reports']}")
print(f"  Accuracy: {stats['accuracy_percent']:.1f}%")
print(f"  Precision: {stats['precision_percent']:.1f}%")
print(f"  Recall: {stats['recall_percent']:.1f}%")

# Show recent activity
recent = feedback_system.get_recent_stats()
print(f"\n⏰ Last 24 hours:")
print(f"  Reports: {recent['count']}")
print(f"  Conditions: {recent['conditions']}")

print("\n" + "="*60)
print("✅ All tests completed!")
print("="*60)
print("\n📌 Next Steps:")
print("  1. Start server: python backend/quick_start_no_ws.py")
print("  2. Test BIFI v2: http://localhost:5000/api/weather/current")
print("  3. View validation: http://localhost:5000/validation")
print("  4. Submit feedback from mobile: http://localhost:5000/mobile")
print("="*60)
