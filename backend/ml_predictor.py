"""
AI/ML Deep Learning Model for Black Ice Prediction
Uses TensorFlow for pattern recognition and historical learning
"""
import os
import json
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TensorFlow imports with fallback
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    TF_AVAILABLE = True
    logger.info("TensorFlow loaded successfully")
except ImportError:
    TF_AVAILABLE = False
    logger.warning("TensorFlow not available - ML predictions disabled")


class MLBlackIcePredictor:
    """
    Deep Learning model for black ice prediction using LSTM neural network
    Learns from historical patterns and weather sequences
    """
    
    def __init__(self, model_path: str = '../models/black_ice_model.h5'):
        self.model_path = model_path
        self.model: Optional[keras.Model] = None
        self.is_trained = False
        self.feature_names = [
            'temperature', 'humidity', 'dew_point', 'wind_speed', 
            'precipitation', 'pressure', 'cloud_cover', 'hour_of_day',
            'day_of_year', 'temp_change_rate'
        ]
        self.sequence_length = 6  # Use 6 hours of historical data
        self.training_history = []
        
        if TF_AVAILABLE:
            self._initialize_model()
        
    def _initialize_model(self):
        """Initialize or load the LSTM neural network"""
        try:
            if os.path.exists(self.model_path):
                self.model = keras.models.load_model(self.model_path)
                self.is_trained = True
                logger.info(f"Loaded pre-trained model from {self.model_path}")
            else:
                self._create_model()
                logger.info("Created new neural network model")
        except Exception as e:
            logger.error(f"Error initializing model: {e}")
            self._create_model()
    
    def _create_model(self):
        """Create a new LSTM model architecture"""
        if not TF_AVAILABLE:
            return
        
        # LSTM model for time series prediction
        model = keras.Sequential([
            # Input layer - sequences of weather data
            layers.Input(shape=(self.sequence_length, len(self.feature_names))),
            
            # First LSTM layer with dropout for regularization
            layers.LSTM(128, return_sequences=True, activation='tanh'),
            layers.Dropout(0.3),
            
            # Second LSTM layer
            layers.LSTM(64, return_sequences=False, activation='tanh'),
            layers.Dropout(0.3),
            
            # Dense layers for classification
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(32, activation='relu'),
            
            # Output layer - probability distribution over 5 risk levels
            layers.Dense(5, activation='softmax')
        ])
        
        # Compile with categorical crossentropy for multi-class classification
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy', 'AUC']
        )
        
        self.model = model
        logger.info("Created LSTM model architecture")
        
    def prepare_features(self, weather_data: Dict) -> np.ndarray:
        """
        Extract and normalize features from weather data
        
        Args:
            weather_data: Dictionary containing weather information
            
        Returns:
            Normalized feature array
        """
        now = datetime.now()
        
        features = [
            weather_data.get('temperature', 0) / 50.0,  # Normalize to [-1, 1] range
            weather_data.get('humidity', 0) / 100.0,
            weather_data.get('dew_point', 0) / 50.0,
            weather_data.get('wind_speed', 0) / 50.0,
            weather_data.get('precipitation', 0) / 10.0,
            weather_data.get('pressure', 1013) / 1100.0,
            weather_data.get('cloud_cover', 0) / 100.0,
            now.hour / 24.0,
            now.timetuple().tm_yday / 365.0,
            weather_data.get('temp_change_rate', 0) / 10.0
        ]
        
        return np.array(features, dtype=np.float32)
    
    def predict(self, weather_sequence: List[Dict]) -> Dict:
        """
        Predict black ice risk using the trained model
        
        Args:
            weather_sequence: List of weather data dictionaries (recent history)
            
        Returns:
            Dictionary with predictions and confidence scores
        """
        if not TF_AVAILABLE or self.model is None:
            return self._fallback_prediction(weather_sequence[-1] if weather_sequence else {})
        
        try:
            # Prepare feature sequences
            features_list = []
            for weather_data in weather_sequence[-self.sequence_length:]:
                features_list.append(self.prepare_features(weather_data))
            
            # Pad if we don't have enough history
            while len(features_list) < self.sequence_length:
                features_list.insert(0, features_list[0] if features_list else np.zeros(len(self.feature_names)))
            
            # Convert to numpy array and add batch dimension
            X = np.array([features_list])
            
            # Make prediction
            predictions = self.model.predict(X, verbose=0)[0]
            
            # Map to risk levels
            risk_levels = ['none', 'low', 'moderate', 'high', 'extreme']
            confidence_scores = {
                level: float(prob) for level, prob in zip(risk_levels, predictions)
            }
            
            # Get primary prediction
            predicted_level = risk_levels[np.argmax(predictions)]
            confidence = float(np.max(predictions))
            
            return {
                'risk_level': predicted_level,
                'confidence': confidence,
                'all_probabilities': confidence_scores,
                'model': 'deep_learning_lstm',
                'is_trained': self.is_trained
            }
            
        except Exception as e:
            logger.error(f"Error in ML prediction: {e}")
            return self._fallback_prediction(weather_sequence[-1] if weather_sequence else {})
    
    def _fallback_prediction(self, weather_data: Dict) -> Dict:
        """Simple rule-based fallback when ML is unavailable"""
        temp = weather_data.get('temperature', 50)
        humidity = weather_data.get('humidity', 50)
        
        # Simple rules
        if temp <= 32 and humidity > 80:
            risk = 'high'
            confidence = 0.75
        elif temp <= 35 and humidity > 70:
            risk = 'moderate'
            confidence = 0.65
        elif temp <= 38:
            risk = 'low'
            confidence = 0.55
        else:
            risk = 'none'
            confidence = 0.60
            
        return {
            'risk_level': risk,
            'confidence': confidence,
            'all_probabilities': {},
            'model': 'rule_based_fallback',
            'is_trained': False
        }
    
    def train(self, training_data: List[Tuple[List[Dict], str]], epochs: int = 50, batch_size: int = 32):
        """
        Train the model on historical data
        
        Args:
            training_data: List of (weather_sequence, risk_level) tuples
            epochs: Number of training epochs
            batch_size: Batch size for training
        """
        if not TF_AVAILABLE or self.model is None:
            logger.warning("Cannot train - TensorFlow not available")
            return
        
        try:
            # Prepare training data
            X_train = []
            y_train = []
            risk_level_map = {'none': 0, 'low': 1, 'moderate': 2, 'high': 3, 'extreme': 4}
            
            for weather_sequence, risk_level in training_data:
                features_list = []
                for weather_data in weather_sequence[-self.sequence_length:]:
                    features_list.append(self.prepare_features(weather_data))
                
                # Pad sequences
                while len(features_list) < self.sequence_length:
                    features_list.insert(0, np.zeros(len(self.feature_names)))
                
                X_train.append(features_list)
                y_train.append(risk_level_map[risk_level])
            
            X_train = np.array(X_train)
            y_train = keras.utils.to_categorical(y_train, num_classes=5)
            
            # Train the model
            logger.info(f"Training model on {len(X_train)} samples...")
            history = self.model.fit(
                X_train, y_train,
                epochs=epochs,
                batch_size=batch_size,
                validation_split=0.2,
                verbose=1,
                callbacks=[
                    keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
                    keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=5)
                ]
            )
            
            self.is_trained = True
            self.training_history.append({
                'timestamp': datetime.now().isoformat(),
                'samples': len(X_train),
                'final_accuracy': float(history.history['accuracy'][-1]),
                'final_loss': float(history.history['loss'][-1])
            })
            
            # Save the trained model
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            self.model.save(self.model_path)
            logger.info(f"Model trained and saved to {self.model_path}")
            
        except Exception as e:
            logger.error(f"Error during training: {e}")
    
    def get_model_info(self) -> Dict:
        """Get information about the current model"""
        return {
            'tensorflow_available': TF_AVAILABLE,
            'model_loaded': self.model is not None,
            'is_trained': self.is_trained,
            'model_path': self.model_path,
            'sequence_length': self.sequence_length,
            'feature_count': len(self.feature_names),
            'features': self.feature_names,
            'training_history': self.training_history[-5:] if self.training_history else []
        }
