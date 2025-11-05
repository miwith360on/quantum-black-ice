"""Test ML Road Surface Temperature Model"""

from ml_road_temp_model import MLRoadSurfaceTempModel

model = MLRoadSurfaceTempModel()

print("🤖 ML ROAD SURFACE TEMPERATURE MODEL TEST")
print("=" * 60)

# Test scenario: Cold bridge at night with satellite data
current_data = {
    'weather': {
        'temperature': 28,
        'humidity': 90,
        'wind_speed': 12,
        'precipitation': 0.05,
        'dew_point': 26,
        'road_surface_temp': 26,  # OpenMeteo estimate
        'soil_temperature': 30,
        'pressure': 1015,
        'latitude': 40.7,
        'longitude': -75.3,
        'cloud_cover': 80
    },
    'satellite': {
        'thermal_temperature': 25,  # NASA satellite sees 25°F
        'ice_signature': 0.7,
        'reflectivity': 0.8
    },
    'quantum': {
        'probability': 0.85,
        'risk_score': 0.9,
        'quantum_metrics': {'entropy': 11.5}
    },
    'traffic': {
        'volume': 'low',
        'heat_dissipation': 0.5,
        'congestion': 0
    },
    'location': {
        'elevation': 250,
        'pavement_type': 'concrete',  # Concrete on bridge
        'shade_factor': 0.9,  # Night, but still dark
        'water_proximity': 0.8,  # Bridge over water!
        'urban_heat_island': 0.1  # Rural area
    }
}

print("\n📊 INPUT DATA:")
print(f"  Air Temperature: {current_data['weather']['temperature']}°F")
print(f"  OpenMeteo Road Estimate: {current_data['weather']['road_surface_temp']}°F")
print(f"  NASA Satellite Thermal: {current_data['satellite']['thermal_temperature']}°F")
print(f"  Quantum Ice Probability: {current_data['quantum']['probability']:.1%}")
print(f"  Traffic Volume: {current_data['traffic']['volume']}")
print(f"  Location: Bridge over water (concrete)")

print("\n🔬 PREPARING 25 ML FEATURES...")
features = model.prepare_features(
    current_data['weather'],
    current_data['satellite'],
    current_data['quantum'],
    current_data['traffic'],
    current_data['location']
)

print(f"  ✅ Feature vector shape: {features.shape}")
print(f"  Sample features: {features[:10]}")

print("\n🤖 RUNNING PREDICTION...")
prediction = model.predict_road_temperature(current_data)

print("\n🎯 PREDICTION RESULTS:")
print("=" * 60)
print(f"  ML Predicted Road Temp: {prediction['predicted_temperature']:.1f}°F")
print(f"  Confidence: {prediction['confidence']:.1%}")
print(f"  Method: {prediction['method']}")
print(f"  Timestamp: {prediction['timestamp']}")

print("\n📈 COMPARISON:")
print(f"  Air Temp:              {current_data['weather']['temperature']}°F")
print(f"  OpenMeteo Estimate:    {current_data['weather']['road_surface_temp']}°F")
print(f"  NASA Satellite:        {current_data['satellite']['thermal_temperature']}°F")
print(f"  ML Prediction:         {prediction['predicted_temperature']:.1f}°F")

print("\n💡 MODEL INFO:")
info = model.get_model_info()
print(f"  Name: {info['name']}")
print(f"  Type: {info['type']}")
print(f"  Trained: {info['is_trained']}")
print(f"  Features: {info['num_features']}")
print(f"  Sequence Length: {info['sequence_length']} hours")
print(f"  Architecture: {info['architecture']}")

print("\n📡 Data Sources:")
for source in info['data_sources']:
    print(f"    • {source}")

print("\n✅ ML Road Temp Model test complete!")
print("\n💡 NOTE: Model not trained yet, using physics-based fallback")
print("   Train with actual data for ML predictions!")
