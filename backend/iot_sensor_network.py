"""
IoT Sensor Network Integration
Connects to smart city infrastructure and IoT devices for real-time black ice detection
Supports: MQTT, REST APIs, WebSockets, and custom protocols
"""

import logging
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SensorType(Enum):
    """Types of IoT sensors"""
    BRIDGE_DECK_TEMP = "bridge_deck_temperature"
    ROAD_SURFACE_TEMP = "road_surface_temperature"
    ROAD_MOISTURE = "road_moisture"
    AIR_TEMP = "air_temperature"
    HUMIDITY = "humidity"
    PRECIPITATION = "precipitation"
    WIND_SPEED = "wind_speed"
    CAMERA_ICE_DETECTION = "camera_ice_detection"
    VEHICLE_TRACTION = "vehicle_traction"
    WEATHER_STATION = "weather_station"


class Protocol(Enum):
    """Communication protocols"""
    MQTT = "mqtt"
    REST_API = "rest"
    WEBSOCKET = "websocket"
    MODBUS = "modbus"
    CUSTOM = "custom"


@dataclass
class Sensor:
    """IoT Sensor data model"""
    sensor_id: str
    sensor_type: SensorType
    location: Dict[str, float]  # {'lat': x, 'lon': y, 'elevation': z}
    protocol: Protocol
    endpoint: str
    last_reading: Optional[Dict] = None
    last_update: Optional[datetime] = None
    is_active: bool = True
    metadata: Optional[Dict] = None


@dataclass
class SensorReading:
    """Sensor reading data"""
    sensor_id: str
    sensor_type: SensorType
    value: float
    unit: str
    timestamp: datetime
    location: Dict[str, float]
    quality: float  # 0-1, data quality score
    metadata: Optional[Dict] = None


class IoTSensorNetwork:
    """
    IoT Sensor Network Integration System
    
    Connects to various IoT devices and smart city infrastructure:
    - Bridge deck temperature sensors
    - Road surface temperature probes
    - Moisture detectors
    - Weather stations
    - Traffic cameras with ice detection
    - Connected vehicle traction data
    """
    
    def __init__(self):
        self.sensors: Dict[str, Sensor] = {}
        self.readings_cache: List[SensorReading] = []
        self.cache_duration = timedelta(hours=1)
        
        # MQTT client (optional)
        self.mqtt_client = None
        
        # Initialize with demo sensors (would be replaced with real sensor registration)
        self._register_demo_sensors()
        
        logger.info("📡 IoT Sensor Network initialized")
    
    def register_sensor(self, sensor: Sensor):
        """Register a new IoT sensor"""
        self.sensors[sensor.sensor_id] = sensor
        logger.info(f"✅ Registered sensor {sensor.sensor_id} ({sensor.sensor_type.value})")
    
    def get_nearby_sensors(self, 
                          lat: float, 
                          lon: float, 
                          radius_km: float = 10,
                          sensor_types: List[SensorType] = None) -> List[Sensor]:
        """
        Get all sensors near a location
        
        Args:
            lat, lon: Location coordinates
            radius_km: Search radius in kilometers
            sensor_types: Optional filter by sensor types
            
        Returns:
            List of nearby sensors
        """
        nearby = []
        
        for sensor in self.sensors.values():
            if not sensor.is_active:
                continue
            
            # Filter by type
            if sensor_types and sensor.sensor_type not in sensor_types:
                continue
            
            # Calculate distance
            distance = self._calculate_distance(
                lat, lon,
                sensor.location['lat'], sensor.location['lon']
            )
            
            if distance <= radius_km:
                nearby.append(sensor)
        
        return nearby
    
    def get_sensor_data(self, 
                       lat: float, 
                       lon: float,
                       radius_km: float = 10) -> Dict:
        """
        Aggregate sensor data for a location
        
        Returns:
            Dict with road conditions from nearby sensors
        """
        
        # Get nearby sensors
        sensors = self.get_nearby_sensors(lat, lon, radius_km)
        
        if not sensors:
            return {
                'sensors_available': False,
                'message': 'No IoT sensors in range',
                'search_radius_km': radius_km
            }
        
        # Fetch latest readings
        readings = {}
        
        for sensor in sensors:
            try:
                reading = self._fetch_sensor_reading(sensor)
                if reading:
                    sensor_type_key = sensor.sensor_type.value
                    if sensor_type_key not in readings:
                        readings[sensor_type_key] = []
                    readings[sensor_type_key].append({
                        'sensor_id': sensor.sensor_id,
                        'value': reading.value,
                        'unit': reading.unit,
                        'timestamp': reading.timestamp.isoformat(),
                        'distance_km': self._calculate_distance(
                            lat, lon,
                            sensor.location['lat'], sensor.location['lon']
                        ),
                        'quality': reading.quality
                    })
            except Exception as e:
                logger.warning(f"Failed to fetch data from {sensor.sensor_id}: {e}")
        
        # Calculate aggregated conditions
        conditions = self._aggregate_conditions(readings)
        
        return {
            'sensors_available': True,
            'num_sensors': len(sensors),
            'search_radius_km': radius_km,
            'readings': readings,
            'aggregated_conditions': conditions,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_bridge_temperature(self, 
                              bridge_lat: float, 
                              bridge_lon: float,
                              bridge_name: str = None) -> Optional[float]:
        """
        Get bridge deck temperature from IoT sensors
        Critical for black ice detection on bridges!
        
        Args:
            bridge_lat, bridge_lon: Bridge location
            bridge_name: Optional bridge identifier
            
        Returns:
            Bridge deck temperature in Fahrenheit, or None if no sensor available
        """
        
        # Look for bridge deck temp sensors within 0.5km
        sensors = self.get_nearby_sensors(
            bridge_lat, bridge_lon, 
            radius_km=0.5,
            sensor_types=[SensorType.BRIDGE_DECK_TEMP]
        )
        
        if not sensors:
            logger.info(f"No bridge deck sensors found near {bridge_name or 'bridge'}")
            return None
        
        # Get most recent reading from closest sensor
        closest_sensor = min(sensors, key=lambda s: self._calculate_distance(
            bridge_lat, bridge_lon,
            s.location['lat'], s.location['lon']
        ))
        
        reading = self._fetch_sensor_reading(closest_sensor)
        
        if reading:
            logger.info(f"🌉 Bridge deck temp: {reading.value}°F (sensor: {closest_sensor.sensor_id})")
            return reading.value
        
        return None
    
    def get_road_moisture(self, lat: float, lon: float) -> Optional[str]:
        """
        Get road moisture level from sensors
        
        Returns:
            Moisture level: 'dry', 'moist', 'wet', 'ice', or None
        """
        
        sensors = self.get_nearby_sensors(
            lat, lon,
            radius_km=2,
            sensor_types=[SensorType.ROAD_MOISTURE]
        )
        
        if not sensors:
            return None
        
        # Get readings from all nearby moisture sensors
        moisture_levels = []
        
        for sensor in sensors:
            reading = self._fetch_sensor_reading(sensor)
            if reading and reading.quality > 0.5:
                moisture_levels.append(reading.value)
        
        if not moisture_levels:
            return None
        
        # Average moisture level
        avg_moisture = sum(moisture_levels) / len(moisture_levels)
        
        # Classify
        if avg_moisture < 0.1:
            return 'dry'
        elif avg_moisture < 0.4:
            return 'moist'
        elif avg_moisture < 0.7:
            return 'wet'
        else:
            return 'ice'  # Very high moisture + cold = ice
    
    def integrate_with_quantum_prediction(self,
                                         lat: float,
                                         lon: float,
                                         quantum_prediction: Dict) -> Dict:
        """
        Enhance quantum prediction with real IoT sensor data
        
        Returns:
            Enhanced prediction with sensor validation
        """
        
        # Get sensor data
        sensor_data = self.get_sensor_data(lat, lon, radius_km=5)
        
        if not sensor_data['sensors_available']:
            return {
                'quantum_prediction': quantum_prediction,
                'sensor_validation': 'No sensors available',
                'confidence_boost': 0
            }
        
        # Extract key measurements
        conditions = sensor_data['aggregated_conditions']
        
        # Calculate confidence boost based on sensor agreement
        confidence_boost = 0
        validations = []
        
        # Validate temperature
        if conditions.get('road_surface_temp'):
            sensor_temp = conditions['road_surface_temp']
            quantum_risk = quantum_prediction.get('probability', 0.5)
            
            if sensor_temp <= 32 and quantum_risk > 0.6:
                confidence_boost += 0.15
                validations.append("Sensor confirms freezing road temp")
            elif sensor_temp > 35 and quantum_risk < 0.4:
                confidence_boost += 0.1
                validations.append("Sensor confirms safe road temp")
        
        # Validate moisture
        if conditions.get('moisture_level'):
            moisture = conditions['moisture_level']
            quantum_risk = quantum_prediction.get('probability', 0.5)
            
            if moisture in ['wet', 'ice'] and quantum_risk > 0.5:
                confidence_boost += 0.2
                validations.append(f"Sensor confirms {moisture} road surface")
            elif moisture == 'dry' and quantum_risk < 0.3:
                confidence_boost += 0.15
                validations.append("Sensor confirms dry road")
        
        # Bridge deck validation
        if conditions.get('bridge_deck_temp'):
            bridge_temp = conditions['bridge_deck_temp']
            if bridge_temp <= 32:
                validations.append(f"⚠️ Bridge deck frozen: {bridge_temp}°F")
                confidence_boost += 0.25  # High confidence - direct measurement!
        
        return {
            'quantum_prediction': quantum_prediction,
            'sensor_data': sensor_data,
            'sensor_validation': validations,
            'confidence_boost': min(confidence_boost, 0.4),  # Cap at 40% boost
            'enhanced_confidence': min(1.0, quantum_prediction.get('confidence', 0.5) + confidence_boost)
        }
    
    def _fetch_sensor_reading(self, sensor: Sensor) -> Optional[SensorReading]:
        """
        Fetch latest reading from a sensor
        In production, this would make actual API calls / MQTT messages
        """
        
        # For demo, generate synthetic data based on sensor type
        # In production, replace with actual sensor communication
        
        try:
            # Check protocol
            if sensor.protocol == Protocol.MQTT:
                return self._fetch_mqtt_reading(sensor)
            elif sensor.protocol == Protocol.REST_API:
                return self._fetch_rest_reading(sensor)
            elif sensor.protocol == Protocol.WEBSOCKET:
                return self._fetch_websocket_reading(sensor)
            else:
                return self._fetch_demo_reading(sensor)
        
        except Exception as e:
            logger.error(f"Failed to fetch from {sensor.sensor_id}: {e}")
            return None
    
    def _fetch_demo_reading(self, sensor: Sensor) -> SensorReading:
        """Generate demo sensor reading"""
        
        # Generate realistic values based on sensor type
        if sensor.sensor_type == SensorType.BRIDGE_DECK_TEMP:
            value = 28.5  # Cold bridge deck
            unit = "°F"
        elif sensor.sensor_type == SensorType.ROAD_SURFACE_TEMP:
            value = 30.2
            unit = "°F"
        elif sensor.sensor_type == SensorType.ROAD_MOISTURE:
            value = 0.75  # High moisture (0-1 scale)
            unit = "moisture_index"
        elif sensor.sensor_type == SensorType.AIR_TEMP:
            value = 32.0
            unit = "°F"
        else:
            value = 0
            unit = "unknown"
        
        return SensorReading(
            sensor_id=sensor.sensor_id,
            sensor_type=sensor.sensor_type,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            location=sensor.location,
            quality=0.9,  # High quality demo data
            metadata={'source': 'demo'}
        )
    
    def _fetch_mqtt_reading(self, sensor: Sensor) -> Optional[SensorReading]:
        """Fetch reading from MQTT sensor (placeholder)"""
        # In production, subscribe to MQTT topic and get latest message
        logger.info(f"MQTT fetch from {sensor.endpoint} (not implemented)")
        return self._fetch_demo_reading(sensor)
    
    def _fetch_rest_reading(self, sensor: Sensor) -> Optional[SensorReading]:
        """Fetch reading from REST API sensor (placeholder)"""
        # In production, make HTTP GET request
        logger.info(f"REST fetch from {sensor.endpoint} (not implemented)")
        return self._fetch_demo_reading(sensor)
    
    def _fetch_websocket_reading(self, sensor: Sensor) -> Optional[SensorReading]:
        """Fetch reading from WebSocket sensor (placeholder)"""
        # In production, connect to WebSocket and get latest data
        logger.info(f"WebSocket fetch from {sensor.endpoint} (not implemented)")
        return self._fetch_demo_reading(sensor)
    
    def _aggregate_conditions(self, readings: Dict) -> Dict:
        """Aggregate sensor readings into overall conditions"""
        
        conditions = {}
        
        # Average road surface temperatures
        if 'road_surface_temperature' in readings:
            temps = [r['value'] for r in readings['road_surface_temperature']]
            conditions['road_surface_temp'] = sum(temps) / len(temps)
        
        # Average bridge deck temperatures
        if 'bridge_deck_temperature' in readings:
            temps = [r['value'] for r in readings['bridge_deck_temperature']]
            conditions['bridge_deck_temp'] = sum(temps) / len(temps)
        
        # Moisture level (worst case)
        if 'road_moisture' in readings:
            moisture_values = [r['value'] for r in readings['road_moisture']]
            max_moisture = max(moisture_values)
            
            if max_moisture < 0.1:
                conditions['moisture_level'] = 'dry'
            elif max_moisture < 0.4:
                conditions['moisture_level'] = 'moist'
            elif max_moisture < 0.7:
                conditions['moisture_level'] = 'wet'
            else:
                conditions['moisture_level'] = 'ice'
        
        return conditions
    
    def _register_demo_sensors(self):
        """Register demo sensors for testing"""
        
        # Bridge deck sensor on I-95 bridge
        self.register_sensor(Sensor(
            sensor_id="BRIDGE_I95_001",
            sensor_type=SensorType.BRIDGE_DECK_TEMP,
            location={'lat': 40.7128, 'lon': -75.0060, 'elevation': 150},
            protocol=Protocol.MQTT,
            endpoint="mqtt://sensors.smartcity.gov/bridge/i95/001",
            metadata={'bridge_name': 'I-95 Delaware River Bridge'}
        ))
        
        # Road surface sensor
        self.register_sensor(Sensor(
            sensor_id="ROAD_TEMP_002",
            sensor_type=SensorType.ROAD_SURFACE_TEMP,
            location={'lat': 40.7200, 'lon': -75.0100, 'elevation': 120},
            protocol=Protocol.REST_API,
            endpoint="https://api.smartcity.gov/sensors/road/002",
            metadata={'highway': 'I-95 Northbound Mile 45'}
        ))
        
        # Moisture detector
        self.register_sensor(Sensor(
            sensor_id="MOISTURE_003",
            sensor_type=SensorType.ROAD_MOISTURE,
            location={'lat': 40.7150, 'lon': -75.0080, 'elevation': 125},
            protocol=Protocol.REST_API,
            endpoint="https://api.smartcity.gov/sensors/moisture/003",
            metadata={'location': 'Bridge approach'}
        ))
        
        logger.info("✅ Registered 3 demo IoT sensors")
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in kilometers"""
        from math import radians, cos, sin, asin, sqrt
        
        # Haversine formula
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        km = 6371 * c
        return km
    
    def get_network_status(self) -> Dict:
        """Get IoT network status"""
        active_sensors = sum(1 for s in self.sensors.values() if s.is_active)
        
        sensor_types = {}
        for sensor in self.sensors.values():
            sensor_type = sensor.sensor_type.value
            sensor_types[sensor_type] = sensor_types.get(sensor_type, 0) + 1
        
        return {
            'total_sensors': len(self.sensors),
            'active_sensors': active_sensors,
            'sensor_types': sensor_types,
            'protocols': {
                'mqtt': sum(1 for s in self.sensors.values() if s.protocol == Protocol.MQTT),
                'rest_api': sum(1 for s in self.sensors.values() if s.protocol == Protocol.REST_API),
                'websocket': sum(1 for s in self.sensors.values() if s.protocol == Protocol.WEBSOCKET)
            }
        }
