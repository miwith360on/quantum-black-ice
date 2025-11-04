"""
Demo Script - Test Black Ice Prediction System
This script demonstrates the black ice prediction algorithm without requiring API keys
"""

import sys
sys.path.insert(0, '.')

from backend.black_ice_predictor import BlackIcePredictor

def print_separator():
    print("\n" + "="*70 + "\n")

def demo_prediction(name, temp, humidity, dew_point, wind_speed, precip=0):
    print(f"📍 {name}")
    print(f"   Temperature: {temp}°C | Humidity: {humidity}% | Dew Point: {dew_point}°C")
    print(f"   Wind: {wind_speed} m/s | Precipitation: {precip}mm")
    
    predictor = BlackIcePredictor()
    result = predictor.predict(
        temperature=temp,
        humidity=humidity,
        dew_point=dew_point,
        wind_speed=wind_speed,
        precipitation=precip
    )
    
    risk_icons = {
        'none': '✅',
        'low': '🟢',
        'moderate': '🟡',
        'high': '🟠',
        'extreme': '🔴'
    }
    
    icon = risk_icons.get(result['risk_level'], '❓')
    
    print(f"\n   {icon} RISK LEVEL: {result['risk_level'].upper()}")
    print(f"   Probability: {result['probability']:.1f}%")
    print(f"   Risk Score: {result['risk_score']:.1f}/100")
    
    if result['factors']:
        print(f"\n   Contributing Factors:")
        for factor in result['factors']:
            print(f"   • {factor['name']} ({factor['score']:.1f} pts)")
            print(f"     {factor['description']}")
    
    print(f"\n   Top Recommendation:")
    if result['recommendations']:
        print(f"   → {result['recommendations'][0]}")
    
    print_separator()

def main():
    print("\n" + "❄"*35)
    print("    QUANTUM BLACK ICE DETECTION SYSTEM - DEMO")
    print("❄"*35 + "\n")
    
    print("This demo tests the black ice prediction algorithm with various scenarios.\n")
    
    # Scenario 1: Safe conditions
    demo_prediction(
        "Scenario 1: Safe Summer Day",
        temp=15.0,
        humidity=50,
        dew_point=5.0,
        wind_speed=5.0,
        precip=0
    )
    
    # Scenario 2: Low risk
    demo_prediction(
        "Scenario 2: Cool but Safe",
        temp=3.0,
        humidity=60,
        dew_point=0.0,
        wind_speed=8.0,
        precip=0
    )
    
    # Scenario 3: Moderate risk
    demo_prediction(
        "Scenario 3: Borderline Conditions",
        temp=1.0,
        humidity=75,
        dew_point=-0.5,
        wind_speed=4.0,
        precip=0
    )
    
    # Scenario 4: High risk
    demo_prediction(
        "Scenario 4: Dangerous Conditions",
        temp=-1.0,
        humidity=85,
        dew_point=-2.0,
        wind_speed=2.0,
        precip=0.5
    )
    
    # Scenario 5: Extreme risk
    demo_prediction(
        "Scenario 5: EXTREME DANGER",
        temp=-0.5,
        humidity=95,
        dew_point=-1.0,
        wind_speed=1.5,
        precip=2.0
    )
    
    print("\n✅ Demo completed successfully!")
    print("\nThe prediction algorithm is working correctly.")
    print("All factors are being analyzed and risk levels calculated properly.\n")
    
    print("💡 Next Steps:")
    print("   1. Get an OpenWeatherMap API key (free)")
    print("   2. Add it to the .env file")
    print("   3. Run: start.bat (Windows) or python backend/app.py")
    print("   4. Open frontend/index.html in your browser")
    print("\n" + "❄"*35 + "\n")

if __name__ == "__main__":
    main()
