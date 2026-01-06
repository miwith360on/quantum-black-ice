"""
Complete Demo: Hybrid BIFI + Validation Dashboard
Shows the full workflow from prediction to validation
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from bifi_calculator_v2 import HybridBIFI
from feedback_system import feedback_system
from datetime import datetime

print("=" * 80)
print("🌨️  BLACK ICE DETECTION - ACCURACY UPGRADE DEMO")
print("=" * 80)
print("\n📅 Date:", datetime.now().strftime("%B %d, %Y at %I:%M %p"))
print("\n" + "=" * 80)

# Initialize
bifi = HybridBIFI()

# Real-world scenario
scenario = {
    "location": "I-95 Bridge, Exit 42",
    "weather": {
        "temp": 32,
        "humidity": 88,
        "dew_point": 30,
        "wind_speed": 18,
        "precip_probability": 0.7,
        "road_temp": 29,
        "is_bridge": True,
        "cloud_cover": 10,
        "hour": 4
    }
}

print("\n🗺️  SCENARIO: Early Morning Commute")
print("-" * 80)
print(f"Location: {scenario['location']}")
print(f"Time: 4:00 AM (rush hour approaching)")
print(f"Air Temperature: {scenario['weather']['temp']}°F")
print(f"Road Temperature: {scenario['weather']['road_temp']}°F")
print(f"Humidity: {scenario['weather']['humidity']}%")
print(f"Wind Speed: {scenario['weather']['wind_speed']} mph")
print(f"Cloud Cover: {scenario['weather']['cloud_cover']}% (clear night)")
print(f"Bridge? YES")

print("\n" + "=" * 80)
print("🔬 HYBRID BIFI v2.0.0 ANALYSIS")
print("=" * 80)

# Calculate risk
result = bifi.calculate(scenario['weather'])
components = result['components']

print("\n📊 FINAL RISK ASSESSMENT:")
print(f"   BIFI Score: {result['bifi_score']:.1f}%")
print(f"   Risk Level: {result['risk_level']}")
print(f"   Color Code: {result['risk_color']}")

print("\n🧮 PROBABILITY BREAKDOWN:")
print(f"   P(surface wet):   {components['p_wet']*100:>5.1f}%")
print(f"   P(surface freeze): {components['p_freeze']*100:>5.1f}%")
print(f"   Bridge multiplier:  {components['bridge_multiplier']:>5.2f}x")
print(f"   Uncertainty adj:    {components['uncertainty_adjustment']:>5.2f}x")
print(f"   ─────────────────")
print(f"   Base risk:         {components['base_risk']*100:>5.1f}%")
print(f"   Final risk:        {components['adjusted_risk']*100:>5.1f}%")

print("\n💡 EXPLANATION:")
lines = result['explanation'].split('\n')
for line in lines:
    print(f"   {line}")

print("\n🔍 WETNESS FEATURES:")
for feat, val in result['features']['wetness'].items():
    if isinstance(val, (int, float)):
        print(f"   • {feat}: {val:.2f}")
    else:
        print(f"   • {feat}: {val}")

print("\n❄️  FREEZE FEATURES:")
for feat, val in result['features']['freeze'].items():
    if isinstance(val, (int, float)):
        print(f"   • {feat}: {val:.2f}")
    else:
        print(f"   • {feat}: {val}")

# Simulate driver feedback
print("\n" + "=" * 80)
print("📱 DRIVER FEEDBACK SIMULATION")
print("=" * 80)

print("\n⏰ 30 minutes later...")
print("Driver reports actual conditions:")

report = feedback_system.submit_report(
    lat=40.7128,
    lon=-74.0060,
    actual_condition="icy",
    predicted_condition=result['risk_level'].lower(),
    predicted_probability=components['adjusted_risk'],
    user_comment=f"Black ice confirmed on {scenario['location']} at 4:30 AM. Very dangerous!"
)

print(f"\n✅ Report submitted successfully!")
print(f"   Report ID: {report['id']}")
print(f"   Timestamp: {report['timestamp']}")
print(f"   Location: ({report['location']['lat']}, {report['location']['lon']})")
print(f"   Actual: {report['actual_condition']}")
print(f"   Predicted: {report.get('predicted_condition', 'N/A')}")

# Get updated stats
print("\n" + "=" * 80)
print("📊 VALIDATION DASHBOARD PREVIEW")
print("=" * 80)

stats = feedback_system.get_accuracy_stats()
print(f"\n📈 Overall Performance:")
print(f"   Total Reports: {stats['total_reports']}")
print(f"   Accuracy: {stats['accuracy_percent']:.1f}%")
print(f"   Precision: {stats['precision_percent']:.1f}%")
print(f"   Recall: {stats['recall_percent']:.1f}%")

print(f"\n🧊 Ice Detection Matrix:")
ice = stats['ice_detection']
print(f"   True Positives:  {ice['true_positives']} (correctly predicted ice)")
print(f"   False Positives: {ice['false_positives']} (false alarms)")
print(f"   False Negatives: {ice['false_negatives']} (missed ice)")

print(f"\n📦 By Condition:")
for condition, cond_stats in stats['by_condition'].items():
    total = cond_stats['total']
    correct = cond_stats['correct']
    percent = (correct / total * 100) if total > 0 else 0
    print(f"   {condition.upper():>5}: {correct}/{total} correct ({percent:.0f}%)")

recent = feedback_system.get_recent_stats()
print(f"\n⏰ Last 24 Hours:")
print(f"   Total reports: {recent['count']}")
if recent['conditions']:
    print(f"   Breakdown:")
    for cond, count in recent['conditions'].items():
        emoji = {'dry': '☀️', 'wet': '💧', 'icy': '🧊', 'snow': '❄️'}.get(cond, '🚗')
        print(f"      {emoji} {cond}: {count}")

print("\n" + "=" * 80)
print("✅ DEMO COMPLETE!")
print("=" * 80)

print("\n🎯 Key Improvements Demonstrated:")
print("   1. ✅ Physics-based probability decomposition")
print("   2. ✅ Explainable components (P(wet) × P(freeze))")
print("   3. ✅ Bridge-specific risk modeling")
print("   4. ✅ Ground-truth feedback collection")
print("   5. ✅ Real-time accuracy validation")

print("\n🌐 Access Points:")
print("   📱 Mobile App: http://localhost:5000")
print("   💻 Desktop: http://localhost:5000/desktop")
print("   📊 Validation: http://localhost:5000/validation")
print("   🗺️  Routes: http://localhost:5000/route-dashboard")

print("\n🚀 Ready for Production!")
print("=" * 80)
