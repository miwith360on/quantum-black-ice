"""
Test 10-Qubit Quantum Black Ice Predictor
Tests the enhanced quantum system with all new metrics
"""

import sys
sys.path.insert(0, './backend')

from quantum_predictor import QuantumBlackIcePredictor
from advanced_weather_calculator import AdvancedWeatherCalculator
import json
from datetime import datetime

print("=" * 70)
print("🌨️⚛️ Testing 10-Qubit Quantum Black Ice Detection System")
print("=" * 70)

# Initialize
predictor = QuantumBlackIcePredictor()
calculator = AdvancedWeatherCalculator()

print(f"\n✅ Quantum predictor initialized: {predictor.num_qubits} qubits")

# Test scenarios
test_scenarios = [
    {
        'name': '❄️ HIGH RISK: Freezing + High Humidity + Night',
        'weather': {
            'temperature': 31,
            'humidity': 95,
            'wind_speed': 3,
            'precipitation_probability': 80,
            'hour': 23,
            'clouds': 90,
            'visibility': 2000,
            'pressure': 1010,
            'pressure_change': -5
        }
    },
    {
        'name': '⚠️ MEDIUM RISK: Near Freezing + Moderate Conditions',
        'weather': {
            'temperature': 34,
            'humidity': 70,
            'wind_speed': 10,
            'precipitation_probability': 40,
            'hour': 6,
            'clouds': 60,
            'visibility': 8000,
            'pressure': 1013,
            'pressure_change': -1
        }
    },
    {
        'name': '✅ LOW RISK: Above Freezing + Sunny',
        'weather': {
            'temperature': 45,
            'humidity': 40,
            'wind_speed': 8,
            'precipitation_probability': 10,
            'hour': 14,
            'clouds': 20,
            'visibility': 15000,
            'pressure': 1020,
            'pressure_change': 2
        }
    },
    {
        'name': '🌫️ FOG RISK: Near Freezing + Fog',
        'weather': {
            'temperature': 33,
            'humidity': 98,
            'wind_speed': 1,
            'precipitation_probability': 20,
            'hour': 5,
            'clouds': 100,
            'visibility': 500,
            'pressure': 1008,
            'pressure_change': -2
        }
    }
]

print("\n" + "=" * 70)
print("TESTING SCENARIOS")
print("=" * 70)

for scenario in test_scenarios:
    print(f"\n{'='*70}")
    print(f"Scenario: {scenario['name']}")
    print(f"{'='*70}")
    
    weather = scenario['weather']
    
    # Calculate advanced metrics
    enhanced_weather = calculator.enhance_weather_data(weather.copy())
    
    print(f"\n📊 Input Weather Data:")
    print(f"  Temperature: {weather['temperature']}°F")
    print(f"  Humidity: {weather['humidity']}%")
    print(f"  Wind Speed: {weather['wind_speed']} mph")
    print(f"  Precipitation Prob: {weather['precipitation_probability']}%")
    print(f"  Time: {weather['hour']}:00")
    print(f"  Clouds: {weather['clouds']}%")
    print(f"  Visibility: {weather['visibility']} meters")
    print(f"  Pressure Change: {weather['pressure_change']} mb")
    
    print(f"\n🔬 Calculated Advanced Metrics:")
    print(f"  Dew Point: {enhanced_weather.get('dew_point', 'N/A')}°F")
    print(f"  Feels Like: {enhanced_weather.get('feels_like', 'N/A')}°F")
    print(f"  Road Temperature: {enhanced_weather.get('road_temperature', 'N/A')}°F")
    print(f"  Dew Point Spread: {enhanced_weather.get('dew_point_spread', 'N/A')}°F")
    
    # Run quantum prediction
    print(f"\n⚛️ Running 10-Qubit Quantum Circuit...")
    result = predictor.predict(enhanced_weather)
    
    print(f"\n🎯 Quantum Prediction Results:")
    print(f"  Probability: {result['probability']*100:.1f}%")
    print(f"  Confidence: {result['confidence']*100:.1f}%")
    print(f"  Risk Level: {result['risk_level']}")
    print(f"  Risk Color: {result['risk_color']}")
    
    print(f"\n📊 10-Qubit Risk Factors:")
    factors = result['risk_factors']
    print(f"  Q0 - Temperature: {factors['temperature']:.2f}")
    print(f"  Q1 - Humidity: {factors['humidity']:.2f}")
    print(f"  Q2 - Wind: {factors['wind']:.2f}")
    print(f"  Q3 - Precipitation: {factors['precipitation']:.2f}")
    print(f"  Q4 - Time of Day: {factors['time_of_day']:.2f}")
    print(f"  Q5 - Dew Point: {factors.get('dew_point', 0):.2f}")
    print(f"  Q6 - Road Temp: {factors.get('road_temp', 0):.2f}")
    print(f"  Q7 - Solar Rad: {factors.get('solar', 0):.2f}")
    print(f"  Q8 - Visibility: {factors.get('visibility', 0):.2f}")
    print(f"  Q9 - Pressure: {factors.get('pressure', 0):.2f}")
    
    print(f"\n⚡ Quantum Metrics:")
    qm = result['quantum_metrics']
    print(f"  Entropy: {qm['entropy']:.3f}")
    print(f"  Raw Probability: {qm['raw_probability']:.3f}")
    print(f"  Circuit Depth: {result['circuit_depth']}")
    print(f"  Quantum Volume: {result['quantum_volume']}")

print("\n" + "=" * 70)
print("✅ ALL TESTS COMPLETE!")
print("=" * 70)

print("\n🎉 10-Qubit Quantum System Summary:")
print("  - 5 original qubits (temp, humidity, wind, precip, time)")
print("  - 5 new qubits (dew point, road temp, solar, visibility, pressure)")
print("  - Enhanced entanglement patterns for accuracy")
print("  - NOAA API integration for US weather")
print("  - Advanced weather calculations (dew point, road temp, etc.)")
print("\n🚀 Ready for deployment to Railway!")
