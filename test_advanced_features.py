"""
Advanced Features Test Script
Tests AI/ML, WebSocket, and Radar integration
"""

import sys
sys.path.insert(0, '..')

from backend.ml_predictor import MLBlackIcePredictor
from backend.radar_service import RadarService
from backend.websocket_server import WebSocketManager
import json

print("=" * 60)
print("🚀 ADVANCED FEATURES TEST")
print("=" * 60)
print()

# Test 1: AI/ML Predictor
print("TEST 1: AI/ML Deep Learning Model")
print("-" * 60)

ml_predictor = MLBlackIcePredictor()
info = ml_predictor.get_model_info()

print(f"TensorFlow Available: {info['tensorflow_available']}")
print(f"Model Loaded: {info['model_loaded']}")
print(f"Is Trained: {info['is_trained']}")
print(f"Sequence Length: {info['sequence_length']}")
print(f"Feature Count: {info['feature_count']}")

# Test prediction
weather_sequence = [
    {
        'temperature': 32.0,
        'humidity': 85.0,
        'dew_point': 30.0,
        'wind_speed': 10.0,
        'precipitation': 0.5,
        'pressure': 1013.0,
        'cloud_cover': 75.0,
        'temp_change_rate': -2.0
    },
    {
        'temperature': 30.0,
        'humidity': 88.0,
        'dew_point': 28.0,
        'wind_speed': 12.0,
        'precipitation': 0.3,
        'pressure': 1012.0,
        'cloud_cover': 80.0,
        'temp_change_rate': -1.5
    },
    {
        'temperature': 28.0,
        'humidity': 90.0,
        'dew_point': 26.0,
        'wind_speed': 15.0,
        'precipitation': 0.1,
        'pressure': 1011.0,
        'cloud_cover': 85.0,
        'temp_change_rate': -1.0
    }
]

print("\nTesting ML Prediction...")
prediction = ml_predictor.predict(weather_sequence)

print(f"Risk Level: {prediction['risk_level'].upper()}")
print(f"Confidence: {prediction['confidence'] * 100:.1f}%")
print(f"Model: {prediction['model']}")

if prediction.get('all_probabilities'):
    print("\nProbability Distribution:")
    for level, prob in prediction['all_probabilities'].items():
        print(f"  {level.capitalize()}: {prob * 100:.1f}%")

print("\n✅ ML Model Test Complete")
print()

# Test 2: Radar Service
print("TEST 2: Satellite & Weather Radar")
print("-" * 60)

radar_service = RadarService()

# Test radar layers
print("Testing RainViewer Radar...")
radar_data = radar_service.get_radar_layers(42.3601, -71.0589)

if radar_data['success']:
    print(f"✅ Radar data retrieved")
    print(f"Provider: {radar_data['radar']['provider']}")
    print(f"Layers available: {len(radar_data['radar']['layers'])}")
    
    if radar_data['alerts']:
        print(f"\nActive Alerts: {len(radar_data['alerts'])}")
        for alert in radar_data['alerts'][:2]:  # Show first 2
            print(f"  - {alert['event']}: {alert['severity']}")
    else:
        print("\nNo active weather alerts")
else:
    print(f"❌ Radar data failed: {radar_data.get('error')}")

# Test satellite imagery
print("\nTesting Satellite Imagery...")
satellite_data = radar_service.get_satellite_imagery(42.3601, -71.0589, 'visible')

if satellite_data['success']:
    print(f"✅ Satellite imagery retrieved")
    print(f"Layer: {satellite_data['layer']['name']}")
    print(f"Available types: {', '.join(satellite_data['available_layers'])}")
else:
    print(f"❌ Satellite data failed: {satellite_data.get('error')}")

# Test composite layers
print("\nTesting Composite Layers...")
composite = radar_service.get_composite_layers(42.3601, -71.0589)

if composite['success']:
    print(f"✅ Composite data retrieved")
    print(f"Weather overlays: {len(composite['weather_overlays'])}")
    for overlay_name in composite['weather_overlays'].keys():
        print(f"  - {overlay_name}")
else:
    print(f"❌ Composite data failed: {composite.get('error')}")

print("\n✅ Radar Service Test Complete")
print()

# Test 3: WebSocket Manager
print("TEST 3: Real-Time WebSocket Server")
print("-" * 60)

ws_manager = WebSocketManager()
stats = ws_manager.get_connection_stats()

print(f"SocketIO Available: {stats['socketio_available']}")
print(f"Active Connections: {stats['active_connections']}")
print(f"Subscribed Locations: {stats['subscribed_locations']}")

if stats['socketio_available']:
    print("\n✅ WebSocket functionality available")
    print("Note: Start the Flask app to test live connections")
else:
    print("\n⚠️ WebSocket not available")
    print("Install with: pip install flask-socketio python-socketio")

print("\n✅ WebSocket Test Complete")
print()

# Summary
print("=" * 60)
print("📊 TEST SUMMARY")
print("=" * 60)

features = [
    ("AI/ML Deep Learning", info['tensorflow_available'] and info['model_loaded']),
    ("Satellite & Radar", radar_data['success'] and satellite_data['success']),
    ("Real-Time WebSocket", stats['socketio_available'])
]

for feature, status in features:
    status_icon = "✅" if status else "⚠️"
    status_text = "READY" if status else "NEEDS SETUP"
    print(f"{status_icon} {feature}: {status_text}")

print()
print("=" * 60)
print("🎉 All tests completed!")
print()
print("Next Steps:")
print("1. Start the backend: python backend/app.py")
print("2. Open advanced-dashboard.html in your browser")
print("3. Watch real-time updates stream in!")
print()
print("📚 See docs/ADVANCED_FEATURES.md for complete guide")
print("=" * 60)
