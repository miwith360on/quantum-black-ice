"""Test Quantum V2 (20-qubit) predictor"""

from quantum_predictor_v2 import QuantumBlackIcePredictorV2

predictor = QuantumBlackIcePredictorV2()

# Test scenario: Bridge on cold night with high humidity
weather = {
    'temperature': 30,  # Below freezing
    'humidity': 85,  # High moisture
    'wind_speed': 10,  # Moderate wind
    'precipitation': 0.1,  # Light precipitation
    'dew_point': 28,
    'road_surface_temp': 29,
    'visibility': 3000
}

location = {
    'bridge_proximity': 0.9,  # On a bridge!
    'traffic_volume': 'low',  # No traffic heat
    'elevation_risk': 0.7,
    'shade_risk': 0.8,
    'water_body_proximity': 0.6
}

print("⚛️ QUANTUM V2 (20-QUBIT) TEST")
print("=" * 50)
print("\nWeather Conditions:")
print(f"  Temperature: {weather['temperature']}°F")
print(f"  Humidity: {weather['humidity']}%")
print(f"  Wind Speed: {weather['wind_speed']} mph")
print(f"  Precipitation: {weather['precipitation']} in")
print(f"  Road Surface Temp: {weather['road_surface_temp']}°F")

print("\nLocation Context:")
print(f"  Bridge Proximity: {location['bridge_proximity']} (ON BRIDGE!)")
print(f"  Traffic Volume: {location['traffic_volume']}")
print(f"  Elevation Risk: {location['elevation_risk']}")

print("\nRunning 20-qubit quantum simulation...")
result = predictor.predict(weather, location)

print("\n🎯 RESULTS:")
print("=" * 50)
print(f"  Ice Probability: {result['probability']:.1%}")
print(f"  Risk Level: {result['risk_level']}")
print(f"  Confidence: {result['confidence']:.1%}")
print(f"  Model Version: {result['model_version']}")

print("\n📊 Quantum Metrics:")
print(f"  Qubits: {result['quantum_metrics']['num_qubits']}")
print(f"  Quantum Volume: {result['quantum_metrics']['quantum_volume']:,} states")
print(f"  Circuit Depth: {result['quantum_metrics']['circuit_depth']}")
print(f"  Entanglement Layers: {result['quantum_metrics']['entanglement_layers']}")
print(f"  Entropy: {result['quantum_metrics']['entropy']:.2f}")

print("\n🔬 Risk Factors (First 10):")
for key, value in list(result['risk_factors'].items())[:10]:
    print(f"  {key}: {value:.3f}")

print("\n✅ Quantum V2 test complete!")
