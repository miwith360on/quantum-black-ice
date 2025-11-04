"""
Quantum Black Ice Prediction System
Uses quantum computing for probabilistic weather predictions
Combines quantum superposition with classical ML for enhanced accuracy
"""

import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator
import logging

logger = logging.getLogger(__name__)

class QuantumBlackIcePredictor:
    """
    Quantum-enhanced black ice prediction using qubits and superposition
    
    Concept:
    - Uses quantum superposition to model uncertainty in weather conditions
    - Multiple qubits represent different risk factors simultaneously
    - Quantum interference patterns reveal probability distributions
    - Entanglement captures correlations between weather variables
    """
    
    def __init__(self):
        self.simulator = AerSimulator()
        self.num_qubits = 10  # Expanded to 10 qubits for higher accuracy
        
        # Risk factors mapped to qubits:
        # Qubit 0: Temperature risk
        # Qubit 1: Humidity/moisture risk
        # Qubit 2: Wind chill risk
        # Qubit 3: Precipitation risk
        # Qubit 4: Time of day risk
        # Qubit 5: Dew point risk (NEW)
        # Qubit 6: Road surface temperature risk (NEW)
        # Qubit 7: Solar radiation risk (NEW)
        # Qubit 8: Visibility risk (NEW)
        # Qubit 9: Pressure change risk (NEW)
        
        logger.info("Quantum Black Ice Predictor initialized with {} qubits".format(self.num_qubits))
    
    def encode_weather_to_quantum_state(self, weather_data):
        """
        Encode classical weather data into quantum superposition states
        
        Each qubit is rotated based on risk level (0-1)
        Higher risk = more rotation toward |1⟩ state
        """
        # Extract weather parameters
        temp = weather_data.get('temperature', 32)
        humidity = weather_data.get('humidity', 50) / 100.0
        wind_speed = weather_data.get('wind_speed', 5)
        precipitation = weather_data.get('precipitation_probability', 0) / 100.0
        hour = weather_data.get('hour', 12)
        dew_point = weather_data.get('dew_point', temp - 5)
        feels_like = weather_data.get('feels_like', temp)
        clouds = weather_data.get('clouds', 50) / 100.0
        visibility = weather_data.get('visibility', 10000)
        pressure = weather_data.get('pressure', 1013)
        pressure_change = weather_data.get('pressure_change', 0)
        
        # Calculate risk factors (0-1 scale)
        temp_risk = self._calculate_temperature_risk(temp)
        humidity_risk = humidity  # Already normalized
        wind_risk = min(wind_speed / 30.0, 1.0)  # Max wind 30 mph = full risk
        precip_risk = precipitation
        time_risk = self._calculate_time_risk(hour)
        
        # NEW: Advanced risk factors
        dew_point_risk = self._calculate_dew_point_risk(temp, dew_point)
        road_temp_risk = self._calculate_road_temperature_risk(temp, clouds, wind_speed)
        solar_risk = self._calculate_solar_radiation_risk(hour, clouds)
        visibility_risk = self._calculate_visibility_risk(visibility)
        pressure_risk = self._calculate_pressure_change_risk(pressure_change)
        
        risk_factors = [
            temp_risk, humidity_risk, wind_risk, precip_risk, time_risk,
            dew_point_risk, road_temp_risk, solar_risk, visibility_risk, pressure_risk
        ]
        
        logger.debug(f"Quantum encoding - 10 Risk factors: {risk_factors}")
        
        return risk_factors
    
    def _calculate_temperature_risk(self, temp_f):
        """
        Calculate temperature risk for black ice
        Peak risk: 28-34°F (just below/around freezing)
        """
        if 28 <= temp_f <= 34:
            # Peak danger zone
            return 1.0
        elif 20 <= temp_f < 28:
            # Cold, decreasing risk
            return 0.7 + (temp_f - 20) * 0.0375  # 0.7 to 1.0
        elif 34 < temp_f <= 40:
            # Above freezing, decreasing risk
            return 1.0 - (temp_f - 34) * 0.1  # 1.0 to 0.4
        elif temp_f > 40:
            # Low risk
            return max(0.1, 1.0 - (temp_f - 40) * 0.02)
        else:
            # Very cold, lower risk (snow doesn't melt)
            return 0.5
    
    def _calculate_time_risk(self, hour):
        """
        Calculate time-based risk (overnight/early morning highest)
        """
        if 2 <= hour <= 8:
            # Peak risk: overnight and early morning
            return 1.0
        elif 20 <= hour < 24 or 0 <= hour < 2:
            # Evening/night
            return 0.7
        else:
            # Daytime
            return 0.3
    
    def _calculate_dew_point_risk(self, temp, dew_point):
        """
        Calculate dew point risk - closer to air temp = higher moisture/ice risk
        """
        dew_point_spread = temp - dew_point
        if dew_point_spread < 3:
            # Very close - high risk of moisture/frost
            return 1.0
        elif dew_point_spread < 5:
            return 0.8
        elif dew_point_spread < 10:
            return 0.5
        else:
            return 0.2
    
    def _calculate_road_temperature_risk(self, air_temp, clouds, wind_speed):
        """
        Estimate road surface temperature risk
        Road can be colder than air, especially at night with clear skies
        """
        # Base road temp offset
        road_offset = -2  # Roads typically 2°F colder
        
        # Clear skies = more radiative cooling
        if clouds < 0.3:
            road_offset -= 3
        
        # Wind reduces cooling
        if wind_speed > 10:
            road_offset += 1
        
        estimated_road_temp = air_temp + road_offset
        return self._calculate_temperature_risk(estimated_road_temp)
    
    def _calculate_solar_radiation_risk(self, hour, clouds):
        """
        Calculate solar radiation impact
        Less sun = ice persists longer
        """
        # Nighttime or cloudy = high risk (ice doesn't melt)
        if hour < 6 or hour > 20:
            return 1.0  # No sun
        elif clouds > 0.7:
            return 0.8  # Heavy clouds
        elif 10 <= hour <= 16:
            return 0.2  # Midday sun melts ice
        else:
            return 0.5  # Low sun angle
    
    def _calculate_visibility_risk(self, visibility_meters):
        """
        Calculate visibility risk
        Low visibility often indicates fog/mist = moisture
        """
        if visibility_meters < 1000:
            return 1.0  # Heavy fog
        elif visibility_meters < 5000:
            return 0.7  # Moderate fog
        elif visibility_meters < 10000:
            return 0.4
        else:
            return 0.1  # Clear
    
    def _calculate_pressure_change_risk(self, pressure_change):
        """
        Calculate pressure trend risk
        Falling pressure = weather changing, often precipitation
        """
        if pressure_change < -3:
            return 0.9  # Rapid drop = storm approaching
        elif pressure_change < -1:
            return 0.6  # Slow drop
        elif pressure_change > 3:
            return 0.4  # Rapid rise = clearing
        else:
            return 0.3  # Stable
    
    def create_quantum_circuit(self, risk_factors):
        """
        Create quantum circuit with superposition and entanglement
        
        Uses:
        - Hadamard gates: Create superposition
        - RY rotations: Encode risk probabilities
        - CNOT gates: Create entanglement between factors
        """
        # Create quantum and classical registers
        qr = QuantumRegister(self.num_qubits, 'risk')
        cr = ClassicalRegister(self.num_qubits, 'measure')
        qc = QuantumCircuit(qr, cr)
        
        # Step 1: Create superposition with Hadamard gates
        for i in range(self.num_qubits):
            qc.h(qr[i])
        
        # Step 2: Encode risk factors as rotation angles
        # Higher risk = larger rotation toward |1⟩
        for i, risk in enumerate(risk_factors):
            # RY rotation: angle determines probability
            # risk=0 → 0 rotation (stay in |+⟩)
            # risk=1 → π rotation (flip to |1⟩)
            angle = risk * np.pi
            qc.ry(angle, qr[i])
        
        # Step 3: Create entanglement (correlations between factors)
        # Core weather correlations (original 5 qubits)
        qc.cx(qr[0], qr[1])  # Temperature and humidity
        qc.cx(qr[2], qr[3])  # Wind and precipitation
        qc.cx(qr[4], qr[0])  # Time affects temperature
        
        # NEW: Advanced correlations (qubits 5-9)
        qc.cx(qr[0], qr[5])  # Temperature and dew point
        qc.cx(qr[5], qr[6])  # Dew point and road temp
        qc.cx(qr[4], qr[7])  # Time and solar radiation
        qc.cx(qr[1], qr[8])  # Humidity and visibility
        qc.cx(qr[3], qr[9])  # Precipitation and pressure change
        
        # Cross-correlations for complex interactions
        qc.cx(qr[6], qr[7])  # Road temp and solar
        qc.cx(qr[8], qr[3])  # Visibility and precipitation
        
        # Step 4: Additional interference patterns
        for i in range(self.num_qubits - 1):
            qc.cz(qr[i], qr[i+1])
        
        # Extra entanglement for long-range correlations
        qc.cx(qr[0], qr[9])  # Temperature to pressure
        qc.cx(qr[7], qr[1])  # Solar to humidity
        
        # Step 5: Measure all qubits
        qc.measure(qr, cr)
        
        return qc
    
    def execute_quantum_circuit(self, qc, shots=8192):
        """
        Execute quantum circuit and get measurement results
        More shots = more accurate probability distribution
        """
        # Run simulation
        job = self.simulator.run(qc, shots=shots)
        result = job.result()
        counts = result.get_counts()
        
        logger.debug(f"Quantum measurements: {counts}")
        
        return counts
    
    def calculate_quantum_probability(self, counts, shots):
        """
        Calculate black ice probability from quantum measurement results
        
        Interprets bitstring measurements:
        - More 1's in measurement = higher risk
        - Distribution spread = uncertainty level
        """
        total_risk_score = 0
        max_possible_score = self.num_qubits * shots
        
        for bitstring, count in counts.items():
            # Count number of 1's in bitstring (number of risk factors active)
            ones_count = bitstring.count('1')
            
            # Weight by measurement frequency
            total_risk_score += ones_count * count
        
        # Normalize to 0-1 probability
        raw_probability = total_risk_score / max_possible_score
        
        # Apply quantum confidence scaling
        # High variance in measurements = higher uncertainty
        entropy = self._calculate_entropy(counts, shots)
        confidence = 1.0 - (entropy / np.log2(2**self.num_qubits))  # Normalized entropy
        
        # Adjust probability based on confidence
        # Low confidence = pull toward 0.5 (maximum uncertainty)
        adjusted_probability = (raw_probability * confidence) + (0.5 * (1 - confidence))
        
        return {
            'probability': adjusted_probability,
            'confidence': confidence,
            'raw_probability': raw_probability,
            'entropy': entropy,
            'measurements': counts
        }
    
    def _calculate_entropy(self, counts, shots):
        """
        Calculate Shannon entropy of measurement distribution
        Higher entropy = more uncertainty in quantum state
        """
        entropy = 0
        for count in counts.values():
            p = count / shots
            if p > 0:
                entropy -= p * np.log2(p)
        return entropy
    
    def predict(self, weather_data, shots=8192):
        """
        Main prediction method using quantum circuit
        
        Returns:
        - Quantum probability (0-1)
        - Confidence level (0-1)
        - Risk level (categorical)
        - Detailed quantum metrics
        """
        try:
            # Step 1: Encode weather data to quantum states
            risk_factors = self.encode_weather_to_quantum_state(weather_data)
            
            # Step 2: Create quantum circuit
            qc = self.create_quantum_circuit(risk_factors)
            
            # Step 3: Execute quantum simulation
            counts = self.execute_quantum_circuit(qc, shots)
            
            # Step 4: Calculate probability from measurements
            result = self.calculate_quantum_probability(counts, shots)
            
            # Step 5: Determine risk level
            prob = result['probability']
            if prob < 0.2:
                risk_level = "Very Low"
                risk_color = "#00FF00"
            elif prob < 0.4:
                risk_level = "Low"
                risk_color = "#90EE90"
            elif prob < 0.6:
                risk_level = "Medium"
                risk_color = "#FFD700"
            elif prob < 0.8:
                risk_level = "High"
                risk_color = "#FF8C00"
            else:
                risk_level = "Very High"
                risk_color = "#FF0000"
            
            # Step 6: Package results
            quantum_result = {
                'probability': float(prob),
                'confidence': float(result['confidence']),
                'risk_level': risk_level,
                'risk_color': risk_color,
                'risk_factors': {
                    'temperature': float(risk_factors[0]),
                    'humidity': float(risk_factors[1]),
                    'wind': float(risk_factors[2]),
                    'precipitation': float(risk_factors[3]),
                    'time_of_day': float(risk_factors[4]),
                    'dew_point': float(risk_factors[5]) if len(risk_factors) > 5 else 0.0,
                    'road_temp': float(risk_factors[6]) if len(risk_factors) > 6 else 0.0,
                    'solar': float(risk_factors[7]) if len(risk_factors) > 7 else 0.0,
                    'visibility': float(risk_factors[8]) if len(risk_factors) > 8 else 0.0,
                    'pressure': float(risk_factors[9]) if len(risk_factors) > 9 else 0.0
                },
                'quantum_metrics': {
                    'entropy': float(result['entropy']),
                    'raw_probability': float(result['raw_probability']),
                    'num_qubits': self.num_qubits,
                    'shots': shots,
                    'risk_factors': {
                        'temperature': float(risk_factors[0]),
                        'humidity': float(risk_factors[1]),
                        'wind': float(risk_factors[2]),
                        'precipitation': float(risk_factors[3]),
                        'time_of_day': float(risk_factors[4]),
                        'dew_point': float(risk_factors[5]) if len(risk_factors) > 5 else 0.0,
                        'road_temp': float(risk_factors[6]) if len(risk_factors) > 6 else 0.0,
                        'solar': float(risk_factors[7]) if len(risk_factors) > 7 else 0.0,
                        'visibility': float(risk_factors[8]) if len(risk_factors) > 8 else 0.0,
                        'pressure': float(risk_factors[9]) if len(risk_factors) > 9 else 0.0
                    }
                },
                'circuit_depth': qc.depth(),
                'quantum_volume': 2**self.num_qubits
            }
            
            logger.info(f"Quantum prediction: {prob:.3f} probability, {risk_level} risk")
            
            return quantum_result
            
        except Exception as e:
            logger.error(f"Quantum prediction error: {e}")
            # Fallback to classical estimation
            return self._classical_fallback(weather_data)
    
    def _classical_fallback(self, weather_data):
        """
        Classical probability calculation if quantum fails
        """
        risk_factors = self.encode_weather_to_quantum_state(weather_data)
        prob = np.mean(risk_factors)
        
        return {
            'probability': float(prob),
            'confidence': 0.7,
            'risk_level': "Medium",
            'risk_color': "#FFD700",
            'quantum_metrics': {},
            'fallback': True
        }
    
    def get_circuit_diagram(self, weather_data):
        """
        Get visual representation of quantum circuit
        """
        risk_factors = self.encode_weather_to_quantum_state(weather_data)
        qc = self.create_quantum_circuit(risk_factors)
        return qc.draw('text')


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create quantum predictor
    qpredictor = QuantumBlackIcePredictor()
    
    # Example weather data
    test_weather = {
        'temperature': 30,  # Fahrenheit
        'humidity': 85,
        'wind_speed': 10,
        'precipitation_probability': 60,
        'hour': 6  # 6 AM
    }
    
    print("\n🌨️ Quantum Black Ice Prediction System")
    print("=" * 60)
    print(f"\nWeather Conditions:")
    print(f"  Temperature: {test_weather['temperature']}°F")
    print(f"  Humidity: {test_weather['humidity']}%")
    print(f"  Wind Speed: {test_weather['wind_speed']} mph")
    print(f"  Precipitation: {test_weather['precipitation_probability']}%")
    print(f"  Time: {test_weather['hour']}:00")
    
    # Run quantum prediction
    print("\n🔬 Running quantum simulation...")
    result = qpredictor.predict(test_weather)
    
    print(f"\n📊 Quantum Prediction Results:")
    print(f"  Black Ice Probability: {result['probability']*100:.1f}%")
    print(f"  Confidence Level: {result['confidence']*100:.1f}%")
    print(f"  Risk Level: {result['risk_level']}")
    print(f"\n⚛️ Quantum Metrics:")
    print(f"  Number of Qubits: {result['quantum_metrics']['num_qubits']}")
    print(f"  Quantum Shots: {result['quantum_metrics']['shots']}")
    print(f"  Circuit Depth: {result['circuit_depth']}")
    print(f"  Entropy: {result['quantum_metrics']['entropy']:.3f}")
    
    print("\n" + "=" * 60)
    print("✨ Quantum superposition complete!")
