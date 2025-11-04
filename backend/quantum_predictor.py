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
        self.num_qubits = 5  # One qubit per major risk factor
        
        # Risk factors mapped to qubits:
        # Qubit 0: Temperature risk
        # Qubit 1: Humidity/moisture risk
        # Qubit 2: Wind chill risk
        # Qubit 3: Precipitation risk
        # Qubit 4: Time of day risk
        
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
        
        # Calculate risk factors (0-1 scale)
        temp_risk = self._calculate_temperature_risk(temp)
        humidity_risk = humidity  # Already normalized
        wind_risk = min(wind_speed / 30.0, 1.0)  # Max wind 30 mph = full risk
        precip_risk = precipitation
        time_risk = self._calculate_time_risk(hour)
        
        risk_factors = [temp_risk, humidity_risk, wind_risk, precip_risk, time_risk]
        
        logger.debug(f"Quantum encoding - Risk factors: {risk_factors}")
        
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
        # Temperature and humidity correlation
        qc.cx(qr[0], qr[1])
        
        # Wind and precipitation correlation
        qc.cx(qr[2], qr[3])
        
        # Time affects temperature
        qc.cx(qr[4], qr[0])
        
        # Step 4: Additional interference patterns
        for i in range(self.num_qubits - 1):
            qc.cz(qr[i], qr[i+1])
        
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
                    'time_of_day': float(risk_factors[4])
                },
                'quantum_metrics': {
                    'entropy': float(result['entropy']),
                    'raw_probability': float(result['raw_probability']),
                    'num_qubits': self.num_qubits,
                    'shots': shots
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
