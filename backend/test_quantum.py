"""
Test script for quantum predictor
"""

from quantum_predictor import QuantumBlackIcePredictor
import json

# Initialize quantum predictor
print("Initializing Quantum Black Ice Predictor...")
predictor = QuantumBlackIcePredictor()

# Test weather data
weather_data = {
    'temperature': 28,
    'humidity': 85,
    'wind_speed': 15,
    'precipitation': 0.2,
    'time_of_day': 22  # 10 PM
}

print(f"\nTest weather conditions:")
print(f"  Temperature: {weather_data['temperature']}°F")
print(f"  Humidity: {weather_data['humidity']}%")
print(f"  Wind Speed: {weather_data['wind_speed']} mph")
print(f"  Precipitation: {weather_data['precipitation']} in")
print(f"  Time: {weather_data['time_of_day']}:00")

print("\n🌀 Running quantum circuit simulation...")
result = predictor.predict(weather_data)

print("\n⚛️ Quantum Prediction Results:")
print(json.dumps(result, indent=2))

print("\n✅ Quantum predictor test complete!")
