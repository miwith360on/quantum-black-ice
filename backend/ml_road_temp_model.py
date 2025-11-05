"""
Machine Learning Road Surface Temperature Model
Uses TensorFlow/Keras LSTM to predict exact road surface temperature
Inputs: satellite thermal, quantum predictions, traffic heat, sun angle, pavement type, weather
"""

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from datetime import datetime, timedelta
import logging
import json
import os
from typing import Dict, List, Tuple
import pickle

logger = logging.getLogger(__name__)


class MLRoadSurfaceTempModel:
    """
    Advanced ML model for road surface temperature prediction
    
    Combines multiple data sources:
    - NASA satellite thermal imagery
    - Quantum weather predictions
    - Traffic heat signatures
    - Solar radiation/sun angle
    - Pavement thermal properties
    - Historical cooling/heating rates
    - Micro-climate factors
    """
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path or 'models/road_surface_temp_lstm.h5'
        self.scaler_path = 'models/road_temp_scaler.pkl'
        self.model = None
        self.scaler = None
        self.is_trained = False
        
        # Feature dimensions
        self.sequence_length = 12  # Use last 12 hours of data
        self.num_features = 25  # 25 input features
        
        # Load model if exists
        self._load_model()
        
        logger.info("🤖 ML Road Surface Temp Model initialized")
    
    def prepare_features(self, 
                        weather_data: Dict,
                        satellite_data: Dict = None,
                        quantum_data: Dict = None,
                        traffic_data: Dict = None,
                        location_context: Dict = None) -> np.ndarray:
        """
        Prepare feature vector from all data sources
        
        25 Features:
        [0-4] Core Weather: temp, humidity, wind_speed, precipitation, dew_point
        [5-7] Surface: road_temp_estimate, soil_temp, pressure
        [8-10] Satellite: thermal_temp, ice_signature, reflectivity
        [11-13] Quantum: probability, risk_score, quantum_entropy
        [14-16] Solar: sun_angle, solar_radiation, cloud_cover
        [17-19] Traffic: volume_score, heat_dissipation, congestion_level
        [20-24] Location: elevation, pavement_type, shade_factor, water_proximity, urban_heat_island
        """
        
        features = []
        
        # === CORE WEATHER (0-4) ===
        features.append(weather_data.get('temperature', 40))
        features.append(weather_data.get('humidity', 50))
        features.append(weather_data.get('wind_speed', 5))
        features.append(weather_data.get('precipitation', 0))
        features.append(weather_data.get('dew_point', weather_data.get('temperature', 40) - 10))
        
        # === SURFACE (5-7) ===
        features.append(weather_data.get('road_surface_temp', weather_data.get('temperature', 40) - 2))
        features.append(weather_data.get('soil_temperature', weather_data.get('temperature', 40) - 5))
        features.append(weather_data.get('pressure', 1013))
        
        # === SATELLITE (8-10) ===
        if satellite_data:
            features.append(satellite_data.get('thermal_temperature', 40))
            features.append(satellite_data.get('ice_signature', 0))
            features.append(satellite_data.get('reflectivity', 0.5))
        else:
            features.extend([40, 0, 0.5])
        
        # === QUANTUM (11-13) ===
        if quantum_data:
            features.append(quantum_data.get('probability', 0.5))
            features.append(quantum_data.get('risk_score', 0.5))
            features.append(quantum_data.get('quantum_metrics', {}).get('entropy', 5))
        else:
            features.extend([0.5, 0.5, 5])
        
        # === SOLAR (14-16) ===
        sun_angle = self._calculate_sun_angle(
            weather_data.get('latitude', 40),
            weather_data.get('longitude', -75)
        )
        features.append(sun_angle)
        features.append(weather_data.get('solar_radiation', sun_angle * 500))
        features.append(weather_data.get('cloud_cover', 50) / 100)
        
        # === TRAFFIC (17-19) ===
        if traffic_data:
            volume = traffic_data.get('volume', 'medium')
            volume_score = {'low': 0.2, 'medium': 0.5, 'heavy': 0.8}.get(volume, 0.5)
            features.append(volume_score)
            features.append(traffic_data.get('heat_dissipation', volume_score * 3))
            features.append(traffic_data.get('congestion', 0))
        else:
            features.extend([0.5, 1.5, 0])
        
        # === LOCATION (20-24) ===
        if location_context:
            features.append(location_context.get('elevation', 100) / 1000)  # Normalize
            pavement = location_context.get('pavement_type', 'asphalt')
            pavement_score = {'concrete': 0.3, 'asphalt': 0.5, 'brick': 0.7}.get(pavement, 0.5)
            features.append(pavement_score)
            features.append(location_context.get('shade_factor', 0.5))
            features.append(location_context.get('water_proximity', 0))
            features.append(location_context.get('urban_heat_island', 0))
        else:
            features.extend([0.1, 0.5, 0.5, 0, 0])
        
        return np.array(features, dtype=np.float32)
    
    def predict_road_temperature(self,
                                 current_data: Dict,
                                 historical_sequence: List[Dict] = None) -> Dict:
        """
        Predict road surface temperature using LSTM model
        
        Args:
            current_data: Current weather/satellite/quantum/traffic data
            historical_sequence: Last 12 hours of data (optional)
            
        Returns:
            Dict with predicted temp, confidence, and contributing factors
        """
        
        if not self.is_trained:
            # Fallback to physics-based estimation
            return self._physics_based_estimate(current_data)
        
        try:
            # Prepare sequence
            if historical_sequence and len(historical_sequence) >= self.sequence_length:
                sequence = []
                for data_point in historical_sequence[-self.sequence_length:]:
                    features = self.prepare_features(
                        data_point.get('weather', {}),
                        data_point.get('satellite'),
                        data_point.get('quantum'),
                        data_point.get('traffic'),
                        data_point.get('location')
                    )
                    sequence.append(features)
                sequence = np.array(sequence)
            else:
                # Use current data repeated (not ideal but works)
                features = self.prepare_features(
                    current_data.get('weather', {}),
                    current_data.get('satellite'),
                    current_data.get('quantum'),
                    current_data.get('traffic'),
                    current_data.get('location')
                )
                sequence = np.tile(features, (self.sequence_length, 1))
            
            # Normalize
            if self.scaler:
                original_shape = sequence.shape
                sequence = self.scaler.transform(sequence.reshape(-1, self.num_features))
                sequence = sequence.reshape(original_shape)
            
            # Reshape for LSTM: (1, sequence_length, num_features)
            sequence = sequence.reshape(1, self.sequence_length, self.num_features)
            
            # Predict
            prediction = self.model.predict(sequence, verbose=0)[0][0]
            
            # Calculate confidence based on data quality
            confidence = self._calculate_confidence(current_data, historical_sequence)
            
            return {
                'predicted_temperature': float(prediction),
                'confidence': confidence,
                'method': 'lstm_ml',
                'model_version': 'v1.0',
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            return self._physics_based_estimate(current_data)
    
    def train_model(self,
                   training_data: List[Dict],
                   validation_split: float = 0.2,
                   epochs: int = 50,
                   batch_size: int = 32) -> Dict:
        """
        Train LSTM model on historical data
        
        Args:
            training_data: List of data points with weather/satellite/quantum/traffic/actual_temp
            validation_split: Fraction of data for validation
            epochs: Training epochs
            batch_size: Batch size
            
        Returns:
            Training history dict
        """
        
        logger.info(f"🤖 Training ML Road Temp Model on {len(training_data)} samples...")
        
        # Prepare sequences
        X, y = self._prepare_training_sequences(training_data)
        
        if X is None or len(X) == 0:
            raise ValueError("No valid training data")
        
        # Fit scaler
        from sklearn.preprocessing import StandardScaler
        self.scaler = StandardScaler()
        X_reshaped = X.reshape(-1, self.num_features)
        self.scaler.fit(X_reshaped)
        X_normalized = self.scaler.transform(X_reshaped)
        X_normalized = X_normalized.reshape(X.shape)
        
        # Build model
        self.model = self._build_lstm_model()
        
        # Train
        history = self.model.fit(
            X_normalized, y,
            validation_split=validation_split,
            epochs=epochs,
            batch_size=batch_size,
            verbose=1
        )
        
        self.is_trained = True
        
        # Save
        self._save_model()
        
        logger.info("✅ ML Road Temp Model trained successfully!")
        
        return {
            'final_loss': float(history.history['loss'][-1]),
            'final_val_loss': float(history.history['val_loss'][-1]),
            'epochs_trained': len(history.history['loss']),
            'samples': len(training_data)
        }
    
    def _build_lstm_model(self) -> keras.Model:
        """Build LSTM neural network architecture"""
        
        model = keras.Sequential([
            # Input layer
            layers.Input(shape=(self.sequence_length, self.num_features)),
            
            # LSTM layers
            layers.LSTM(128, return_sequences=True),
            layers.Dropout(0.2),
            
            layers.LSTM(64, return_sequences=True),
            layers.Dropout(0.2),
            
            layers.LSTM(32),
            layers.Dropout(0.2),
            
            # Dense layers
            layers.Dense(16, activation='relu'),
            layers.Dense(8, activation='relu'),
            
            # Output layer (single value: road temp)
            layers.Dense(1)
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def _prepare_training_sequences(self, training_data: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Convert training data into sequences"""
        
        X = []
        y = []
        
        for i in range(len(training_data) - self.sequence_length):
            sequence = []
            for j in range(self.sequence_length):
                data_point = training_data[i + j]
                features = self.prepare_features(
                    data_point.get('weather', {}),
                    data_point.get('satellite'),
                    data_point.get('quantum'),
                    data_point.get('traffic'),
                    data_point.get('location')
                )
                sequence.append(features)
            
            X.append(sequence)
            # Target is actual road temp at end of sequence
            y.append(training_data[i + self.sequence_length].get('actual_road_temp', 32))
        
        return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)
    
    def _physics_based_estimate(self, data: Dict) -> Dict:
        """Fallback physics-based road temp estimation"""
        
        weather = data.get('weather', {})
        air_temp = weather.get('temperature', 40)
        wind_speed = weather.get('wind_speed', 5)
        solar = weather.get('solar_radiation', 0)
        
        # Road typically 2-5°F cooler than air at night
        # Can be 20-40°F warmer in direct sun
        hour = datetime.now().hour
        
        if 22 <= hour or hour <= 6:
            # Night - road cooler
            road_temp = air_temp - 3 - (wind_speed * 0.2)
        elif 10 <= hour <= 16:
            # Day - solar heating
            road_temp = air_temp + (solar / 50)
        else:
            # Dawn/dusk
            road_temp = air_temp - 1
        
        return {
            'predicted_temperature': round(road_temp, 1),
            'confidence': 0.6,
            'method': 'physics_estimate',
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_sun_angle(self, lat: float, lon: float) -> float:
        """Calculate sun angle above horizon (0-90 degrees)"""
        
        now = datetime.now()
        hour = now.hour + now.minute / 60
        
        # Simple approximation
        # Peak sun at noon, 0 at night
        if 6 <= hour <= 18:
            # Daytime
            time_from_noon = abs(12 - hour)
            angle = 90 - (time_from_noon * 7.5)  # ~90° at noon, ~0° at 6am/6pm
            return max(0, angle)
        else:
            return 0
    
    def _calculate_confidence(self, current_data: Dict, historical: List[Dict]) -> float:
        """Calculate prediction confidence based on data quality"""
        
        confidence = 0.5
        
        # Boost confidence if we have satellite data
        if current_data.get('satellite'):
            confidence += 0.15
        
        # Boost if we have quantum prediction
        if current_data.get('quantum'):
            confidence += 0.1
        
        # Boost if we have traffic data
        if current_data.get('traffic'):
            confidence += 0.1
        
        # Boost if we have full historical sequence
        if historical and len(historical) >= self.sequence_length:
            confidence += 0.15
        
        return min(1.0, confidence)
    
    def _save_model(self):
        """Save model and scaler to disk"""
        
        os.makedirs('models', exist_ok=True)
        
        if self.model:
            self.model.save(self.model_path)
            logger.info(f"💾 Model saved to {self.model_path}")
        
        if self.scaler:
            with open(self.scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            logger.info(f"💾 Scaler saved to {self.scaler_path}")
    
    def _load_model(self):
        """Load model and scaler from disk"""
        
        try:
            if os.path.exists(self.model_path):
                self.model = keras.models.load_model(self.model_path)
                self.is_trained = True
                logger.info(f"✅ Model loaded from {self.model_path}")
            
            if os.path.exists(self.scaler_path):
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                logger.info(f"✅ Scaler loaded from {self.scaler_path}")
        
        except Exception as e:
            logger.warning(f"Could not load model: {e}")
            self.is_trained = False
    
    def get_model_info(self) -> Dict:
        """Get model information"""
        
        return {
            'name': 'ML Road Surface Temperature Model',
            'type': 'LSTM Neural Network',
            'is_trained': self.is_trained,
            'sequence_length': self.sequence_length,
            'num_features': self.num_features,
            'architecture': '128->64->32 LSTM + Dense',
            'data_sources': [
                'NASA Satellite Thermal',
                'Quantum Weather Predictions',
                'Traffic Heat Signatures',
                'Solar Radiation/Sun Angle',
                'Pavement Thermal Properties',
                'Micro-climate Factors'
            ]
        }
