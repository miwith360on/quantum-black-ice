"""Test IoT Sensor Network"""

from iot_sensor_network import IoTSensorNetwork, SensorType

network = IoTSensorNetwork()

print("📡 IOT SENSOR NETWORK TEST")
print("=" * 60)

# Get network status
status = network.get_network_status()
print("\n🌐 NETWORK STATUS:")
print(f"  Total Sensors: {status['total_sensors']}")
print(f"  Active Sensors: {status['active_sensors']}")
print(f"  Sensor Types: {status['sensor_types']}")
print(f"  Protocols: {status['protocols']}")

# Test location: Near Philadelphia (where demo sensors are)
test_lat = 40.7150
test_lon = -75.0080

print(f"\n📍 TEST LOCATION: {test_lat}, {test_lon}")

# Get nearby sensors
print("\n🔍 FINDING NEARBY SENSORS...")
nearby = network.get_nearby_sensors(test_lat, test_lon, radius_km=10)
print(f"  Found {len(nearby)} sensors within 10km")

for sensor in nearby:
    print(f"\n  Sensor: {sensor.sensor_id}")
    print(f"    Type: {sensor.sensor_type.value}")
    print(f"    Protocol: {sensor.protocol.value}")
    print(f"    Location: {sensor.location}")
    print(f"    Endpoint: {sensor.endpoint}")

# Get aggregated sensor data
print("\n📊 FETCHING SENSOR DATA...")
data = network.get_sensor_data(test_lat, test_lon, radius_km=10)

print(f"\n🎯 AGGREGATED CONDITIONS:")
if data['sensors_available']:
    print(f"  Sensors in Range: {data['num_sensors']}")
    print(f"  Search Radius: {data['search_radius_km']} km")
    
    conditions = data['aggregated_conditions']
    if 'road_surface_temp' in conditions:
        print(f"  Road Surface Temp: {conditions['road_surface_temp']:.1f}°F")
    if 'bridge_deck_temp' in conditions:
        print(f"  Bridge Deck Temp: {conditions['bridge_deck_temp']:.1f}°F ⚠️")
    if 'moisture_level' in conditions:
        print(f"  Road Moisture: {conditions['moisture_level']}")
    
    print(f"\n📡 SENSOR READINGS:")
    for sensor_type, readings in data['readings'].items():
        print(f"\n  {sensor_type}:")
        for reading in readings:
            print(f"    • Sensor {reading['sensor_id']}: {reading['value']} {reading['unit']}")
            print(f"      Distance: {reading['distance_km']:.2f} km, Quality: {reading['quality']:.0%}")
else:
    print(f"  ❌ No sensors available")

# Test bridge temperature lookup
print("\n🌉 BRIDGE DECK TEMPERATURE TEST:")
bridge_temp = network.get_bridge_temperature(
    test_lat, test_lon, 
    bridge_name="Test Bridge"
)

if bridge_temp:
    print(f"  Bridge Deck: {bridge_temp}°F")
    if bridge_temp <= 32:
        print(f"  ⚠️ WARNING: BRIDGE FREEZING!")
else:
    print(f"  No bridge deck sensor available")

# Test moisture detection
print("\n💧 ROAD MOISTURE TEST:")
moisture = network.get_road_moisture(test_lat, test_lon)
if moisture:
    print(f"  Moisture Level: {moisture}")
    if moisture in ['wet', 'ice']:
        print(f"  ⚠️ WARNING: HAZARDOUS CONDITIONS!")
else:
    print(f"  No moisture sensors available")

# Test quantum integration
print("\n⚛️ QUANTUM + IOT INTEGRATION TEST:")

fake_quantum_prediction = {
    'probability': 0.78,
    'risk_level': 'High',
    'confidence': 0.65
}

enhanced = network.integrate_with_quantum_prediction(
    test_lat, test_lon,
    fake_quantum_prediction
)

print(f"  Original Quantum Confidence: {fake_quantum_prediction['confidence']:.1%}")
print(f"  IoT Confidence Boost: +{enhanced['confidence_boost']:.1%}")
print(f"  Enhanced Confidence: {enhanced['enhanced_confidence']:.1%}")

if enhanced['sensor_validation']:
    print(f"\n  Sensor Validations:")
    for validation in enhanced['sensor_validation']:
        print(f"    ✓ {validation}")

print("\n✅ IoT Sensor Network test complete!")
