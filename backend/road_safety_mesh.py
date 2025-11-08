"""
AI Road Safety Mesh Network
Crowd-sourced road temperature and condition data from IoT sensors
"""

import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple
import random

logger = logging.getLogger(__name__)

class RoadSafetyMeshNetwork:
    """
    Simulates and manages IoT sensor mesh network for road conditions
    Provides real-time temperature, friction, and humidity data
    """
    
    def __init__(self):
        self.sensors = {}  # sensor_id -> sensor_data
        self.sensor_history = {}  # sensor_id -> list of readings
        self.confidence_zones = {}  # zone_id -> confidence_score
        logger.info("Road Safety Mesh Network initialized")
        
    def create_simulated_sensors(self, center_lat, center_lon, radius_miles=10, count=15):
        """
        Create simulated IoT sensor nodes around a location
        
        Args:
            center_lat: Center latitude
            center_lon: Center longitude
            radius_miles: Radius to spread sensors
            count: Number of sensors to create
        
        Returns:
            List of sensor IDs
        """
        sensor_ids = []
        
        for i in range(count):
            # Generate random position within radius
            angle = random.uniform(0, 2 * np.pi)
            distance = random.uniform(0, radius_miles) / 69.0  # Rough miles to degrees
            
            lat = center_lat + distance * np.cos(angle)
            lon = center_lon + distance * np.sin(angle)
            
            sensor_id = f"SENSOR_{center_lat:.2f}_{center_lon:.2f}_{i:03d}"
            
            # Determine sensor type based on location
            sensor_type = self._assign_sensor_type(i)
            
            self.sensors[sensor_id] = {
                'id': sensor_id,
                'type': sensor_type,
                'location': {'lat': lat, 'lon': lon},
                'status': 'active',
                'last_update': datetime.now().isoformat(),
                'readings': {
                    'temperature': None,
                    'friction_index': None,
                    'humidity': None,
                    'surface_temp': None
                }
            }
            
            sensor_ids.append(sensor_id)
            logger.info(f"Created {sensor_type} sensor: {sensor_id}")
            
        return sensor_ids
    
    def _assign_sensor_type(self, index):
        """Assign sensor type based on common road infrastructure"""
        types = ['highway', 'bridge', 'intersection', 'rural_road', 'tunnel']
        # Higher probability for bridges and intersections (critical zones)
        if index % 3 == 0:
            return 'bridge'
        elif index % 4 == 0:
            return 'intersection'
        else:
            return random.choice(types)
    
    def update_sensor_reading(self, sensor_id, temperature=None, friction=None, 
                             humidity=None, surface_temp=None):
        """
        Update sensor with new reading
        
        Args:
            sensor_id: Sensor identifier
            temperature: Air temperature (F)
            friction: Friction index (0-1, where 1 = dry, 0 = ice)
            humidity: Relative humidity (%)
            surface_temp: Road surface temperature (F)
        
        Returns:
            Updated sensor data
        """
        if sensor_id not in self.sensors:
            return {'error': 'Sensor not found'}
        
        sensor = self.sensors[sensor_id]
        
        # Update readings
        if temperature is not None:
            sensor['readings']['temperature'] = temperature
        if friction is not None:
            sensor['readings']['friction_index'] = friction
        if humidity is not None:
            sensor['readings']['humidity'] = humidity
        if surface_temp is not None:
            sensor['readings']['surface_temp'] = surface_temp
            
        sensor['last_update'] = datetime.now().isoformat()
        
        # Store in history
        if sensor_id not in self.sensor_history:
            self.sensor_history[sensor_id] = []
        
        self.sensor_history[sensor_id].append({
            'timestamp': sensor['last_update'],
            'readings': sensor['readings'].copy()
        })
        
        # Keep only last 100 readings
        if len(self.sensor_history[sensor_id]) > 100:
            self.sensor_history[sensor_id] = self.sensor_history[sensor_id][-100:]
        
        logger.info(f"Sensor {sensor_id} updated: {temperature}°F, friction={friction}")
        
        return sensor
    
    def simulate_sensor_readings(self, base_weather):
        """
        Simulate realistic sensor readings based on weather conditions
        
        Args:
            base_weather: Dict with temperature, humidity, wind_speed
        
        Returns:
            Number of sensors updated
        """
        base_temp = base_weather.get('temperature', 32)
        base_humidity = base_weather.get('humidity', 70)
        
        updated = 0
        
        for sensor_id, sensor in self.sensors.items():
            # Add realistic variations based on sensor type
            temp_variation = self._get_temp_variation(sensor['type'])
            sensor_temp = base_temp + random.uniform(-temp_variation, temp_variation)
            
            # Calculate surface temp (usually colder than air)
            surface_temp = sensor_temp - random.uniform(2, 8)
            
            # Calculate friction index based on conditions
            friction = self._calculate_friction_index(sensor_temp, surface_temp, base_humidity)
            
            # Update sensor
            self.update_sensor_reading(
                sensor_id,
                temperature=round(sensor_temp, 1),
                friction=round(friction, 2),
                humidity=round(base_humidity + random.uniform(-5, 5), 1),
                surface_temp=round(surface_temp, 1)
            )
            
            updated += 1
        
        logger.info(f"Simulated readings for {updated} sensors")
        return updated
    
    def _get_temp_variation(self, sensor_type):
        """Get temperature variation range based on sensor type"""
        variations = {
            'bridge': 5.0,  # Bridges can be much colder
            'tunnel': 2.0,  # Tunnels more stable
            'highway': 3.0,
            'intersection': 3.5,
            'rural_road': 4.0
        }
        return variations.get(sensor_type, 3.0)
    
    def _calculate_friction_index(self, air_temp, surface_temp, humidity):
        """
        Calculate road friction index (0-1)
        0 = ice/no friction, 1 = dry/max friction
        """
        # Ice likely when surface temp < 32°F and humidity > 60%
        if surface_temp <= 32 and humidity > 60:
            # Very low friction
            return random.uniform(0.1, 0.3)
        elif surface_temp <= 32:
            # Some ice possible
            return random.uniform(0.3, 0.5)
        elif surface_temp <= 40 and humidity > 80:
            # Wet, slippery conditions
            return random.uniform(0.5, 0.7)
        else:
            # Normal to dry conditions
            return random.uniform(0.7, 1.0)
    
    def get_sensors_in_area(self, lat, lon, radius_miles=5):
        """
        Get all sensors within radius of location
        
        Args:
            lat: Center latitude
            lon: Center longitude
            radius_miles: Search radius
        
        Returns:
            List of sensors with readings
        """
        nearby = []
        
        for sensor_id, sensor in self.sensors.items():
            distance = self._haversine_distance(
                lat, lon,
                sensor['location']['lat'],
                sensor['location']['lon']
            )
            
            if distance <= radius_miles:
                nearby.append({
                    **sensor,
                    'distance_miles': round(distance, 2)
                })
        
        # Sort by distance
        nearby.sort(key=lambda x: x['distance_miles'])
        
        return nearby
    
    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points in miles"""
        R = 3959  # Earth radius in miles
        
        lat1_rad = np.radians(lat1)
        lat2_rad = np.radians(lat2)
        delta_lat = np.radians(lat2 - lat1)
        delta_lon = np.radians(lon2 - lon1)
        
        a = np.sin(delta_lat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c
    
    def calculate_confidence_zones(self, lat, lon, grid_size=5, radius_miles=10):
        """
        Calculate confidence scores based on sensor density
        
        Args:
            lat: Center latitude
            lon: Center longitude
            grid_size: Grid dimensions
            radius_miles: Analysis radius
        
        Returns:
            Confidence matrix (0-1, where 1 = high sensor density)
        """
        confidence_matrix = np.zeros((grid_size, grid_size))
        
        # Create grid boundaries
        lat_step = (radius_miles / 69.0) * 2 / grid_size
        lon_step = (radius_miles / 69.0) * 2 / grid_size
        
        for i in range(grid_size):
            for j in range(grid_size):
                cell_lat = lat - radius_miles/69.0 + i * lat_step
                cell_lon = lon - radius_miles/69.0 + j * lon_step
                
                # Count sensors in this cell
                sensors_in_cell = self.get_sensors_in_area(
                    cell_lat, cell_lon, 
                    radius_miles=radius_miles/grid_size
                )
                
                # Calculate confidence (0-1)
                # 3+ sensors = full confidence
                sensor_count = len(sensors_in_cell)
                confidence = min(sensor_count / 3.0, 1.0)
                
                confidence_matrix[i, j] = confidence
        
        return confidence_matrix
    
    def get_mesh_network_summary(self, lat, lon, radius_miles=10):
        """
        Get summary of mesh network status around location
        
        Returns:
            Dict with network statistics and alerts
        """
        nearby_sensors = self.get_sensors_in_area(lat, lon, radius_miles)
        
        if not nearby_sensors:
            return {
                'total_sensors': 0,
                'active_sensors': 0,
                'freeze_alerts': [],
                'confidence': 'LOW',
                'message': '⚠️ No sensors in area - relying on satellite data'
            }
        
        # Count freeze warnings
        freeze_count = 0
        freeze_locations = []
        
        for sensor in nearby_sensors:
            surface_temp = sensor['readings'].get('surface_temp')
            friction = sensor['readings'].get('friction_index')
            
            if surface_temp and surface_temp <= 32:
                freeze_count += 1
                freeze_locations.append({
                    'type': sensor['type'],
                    'distance': sensor['distance_miles'],
                    'surface_temp': surface_temp,
                    'friction': friction
                })
        
        # Determine confidence level
        sensor_count = len(nearby_sensors)
        if sensor_count >= 5:
            confidence = 'HIGH'
        elif sensor_count >= 3:
            confidence = 'MEDIUM'
        else:
            confidence = 'LOW'
        
        # Generate message
        if freeze_count >= 3:
            message = f"⚠️ {freeze_count} sensors confirm below-freezing conditions"
        elif freeze_count > 0:
            message = f"🔔 {freeze_count} sensor(s) reporting freeze risk"
        else:
            message = f"✅ {sensor_count} sensors - no freeze detected"
        
        return {
            'total_sensors': len(self.sensors),
            'nearby_sensors': sensor_count,
            'active_sensors': sensor_count,
            'freeze_alerts': freeze_locations,
            'confidence': confidence,
            'message': message,
            'sensor_density': round(sensor_count / (radius_miles ** 2), 2),
            'coverage_radius_miles': radius_miles
        }
    
    def export_sensor_data_for_ml(self):
        """
        Export sensor data in format suitable for ML training
        
        Returns:
            List of training samples
        """
        training_data = []
        
        for sensor_id, history in self.sensor_history.items():
            sensor = self.sensors[sensor_id]
            
            for reading in history:
                if all(reading['readings'].values()):  # All fields present
                    training_data.append({
                        'sensor_type': sensor['type'],
                        'temperature': reading['readings']['temperature'],
                        'surface_temp': reading['readings']['surface_temp'],
                        'humidity': reading['readings']['humidity'],
                        'friction_index': reading['readings']['friction_index'],
                        'timestamp': reading['timestamp'],
                        'ice_present': reading['readings']['friction_index'] < 0.4
                    })
        
        return training_data
