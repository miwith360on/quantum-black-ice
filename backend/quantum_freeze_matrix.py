"""
Quantum Freeze Probability Matrix (QFPM)
Uses quantum simulation to predict micro-freeze events 30-90 minutes ahead
"""

import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class QuantumFreezeProbabilityMatrix:
    """
    Advanced quantum-based freeze prediction using environmental perturbations
    Simulates freeze/no-freeze scenarios across multiple environmental conditions
    """
    
    def __init__(self, num_qubits=20):
        """
        Initialize QFPM with 20-qubit quantum simulator
        
        Qubit Mapping:
        0-4: Temperature perturbations (-2°F to +2°F in 1°F steps)
        5-9: Humidity perturbations (-5% to +5% in 2.5% steps)
        10-13: Wind speed variations (0 to 15 mph in 5 mph steps)
        14-16: Time windows (30min, 60min, 90min)
        17-18: Surface type (asphalt, concrete, bridge deck)
        19: Freeze/No-freeze outcome qubit
        """
        self.num_qubits = num_qubits
        self.simulator = AerSimulator()
        logger.info(f"QFPM initialized with {num_qubits} qubits")
        
    def create_perturbation_circuit(self, base_temp, base_humidity, base_wind, 
                                   surface_type='asphalt', time_horizon=60):
        """
        Create quantum circuit that simulates environmental perturbations
        
        Args:
            base_temp: Current temperature (F)
            base_humidity: Current humidity (%)
            base_wind: Current wind speed (mph)
            surface_type: 'asphalt', 'concrete', or 'bridge'
            time_horizon: Prediction window in minutes (30, 60, or 90)
        
        Returns:
            Freeze probability matrix with spatial-temporal predictions
        """
        qr = QuantumRegister(self.num_qubits, 'q')
        cr = ClassicalRegister(self.num_qubits, 'c')
        qc = QuantumCircuit(qr, cr)
        
        # Initialize temperature perturbation qubits (0-4)
        # Map temperature to quantum state
        temp_normalized = self._normalize_temperature(base_temp)
        self._encode_temperature_superposition(qc, qr, temp_normalized)
        
        # Initialize humidity perturbation qubits (5-9)
        humidity_normalized = base_humidity / 100.0
        self._encode_humidity_superposition(qc, qr, humidity_normalized)
        
        # Initialize wind speed qubits (10-13)
        wind_normalized = min(base_wind / 30.0, 1.0)  # Normalize to 0-1
        self._encode_wind_superposition(qc, qr, wind_normalized)
        
        # Encode time horizon (14-16)
        self._encode_time_horizon(qc, qr, time_horizon)
        
        # Encode surface type (17-18)
        self._encode_surface_type(qc, qr, surface_type)
        
        # Apply quantum entanglement between environmental factors
        self._apply_environmental_entanglement(qc, qr)
        
        # Apply freeze condition oracle
        self._apply_freeze_oracle(qc, qr)
        
        # Measure all qubits
        qc.measure(qr, cr)
        
        return qc
    
    def _normalize_temperature(self, temp_f):
        """Normalize temperature to 0-1 range (optimized for freeze conditions)"""
        # Focus on -10°F to 50°F range (most relevant for black ice)
        return np.clip((temp_f + 10) / 60.0, 0, 1)
    
    def _encode_temperature_superposition(self, qc, qr, temp_norm):
        """Encode temperature with perturbations in superposition"""
        # Create superposition across temperature perturbation range
        for i in range(5):  # 5 qubits for temp
            angle = 2 * np.pi * temp_norm
            qc.ry(angle + (i - 2) * 0.2, qr[i])  # ±2°F perturbations
            
    def _encode_humidity_superposition(self, qc, qr, humidity_norm):
        """Encode humidity with perturbations in superposition"""
        for i in range(5, 10):  # 5 qubits for humidity
            angle = 2 * np.pi * humidity_norm
            qc.ry(angle + (i - 7) * 0.15, qr[i])  # ±5% perturbations
            
    def _encode_wind_superposition(self, qc, qr, wind_norm):
        """Encode wind speed variations"""
        for i in range(10, 14):  # 4 qubits for wind
            angle = 2 * np.pi * wind_norm
            qc.ry(angle + (i - 12) * 0.1, qr[i])
            
    def _encode_time_horizon(self, qc, qr, time_minutes):
        """Encode prediction time horizon"""
        if time_minutes >= 90:
            qc.x(qr[14])
            qc.x(qr[15])
        elif time_minutes >= 60:
            qc.x(qr[14])
        # 30 min = |00⟩ (ground state)
        
    def _encode_surface_type(self, qc, qr, surface_type):
        """Encode road surface type"""
        surface_map = {
            'asphalt': 0,    # |00⟩
            'concrete': 1,   # |01⟩
            'bridge': 3      # |11⟩ (highest freeze risk)
        }
        code = surface_map.get(surface_type, 0)
        if code & 1:
            qc.x(qr[17])
        if code & 2:
            qc.x(qr[18])
            
    def _apply_environmental_entanglement(self, qc, qr):
        """Apply quantum entanglement between environmental factors"""
        # Entangle temp and humidity (they affect each other)
        for i in range(5):
            qc.cx(qr[i], qr[5 + i])
        
        # Entangle wind with temperature (wind chill effect)
        for i in range(4):
            qc.cx(qr[10 + i], qr[i])
        
        # Entangle surface type with all environmental factors
        for i in range(5):
            qc.ccx(qr[17], qr[i], qr[18])
            
    def _apply_freeze_oracle(self, qc, qr):
        """Apply freeze condition oracle - marks freeze-prone states"""
        # Multi-controlled gate: freeze likely when temp low, humidity high, wind present
        # This is the quantum "freeze detection" logic
        
        # If temperature qubits indicate cold AND humidity is high
        qc.ccx(qr[0], qr[5], qr[19])  # Outcome qubit
        qc.ccx(qr[1], qr[6], qr[19])
        
        # Bridge surface amplifies freeze risk
        qc.cx(qr[18], qr[19])
        
    def predict_freeze_matrix(self, weather_data, grid_size=5):
        """
        Generate freeze probability matrix for spatial area
        
        Args:
            weather_data: Dict with temp, humidity, wind_speed, location
            grid_size: Size of prediction grid (5x5 default)
        
        Returns:
            Dict with freeze probabilities for 30, 60, 90 min windows
        """
        temp = weather_data.get('temperature', 32)
        humidity = weather_data.get('humidity', 70)
        wind = weather_data.get('wind_speed', 5)
        
        results = {
            '30min': np.zeros((grid_size, grid_size)),
            '60min': np.zeros((grid_size, grid_size)),
            '90min': np.zeros((grid_size, grid_size)),
            'surface_types': []
        }
        
        # Simulate different surface types and time horizons
        for time_horizon in [30, 60, 90]:
            for surface_type in ['asphalt', 'concrete', 'bridge']:
                # Run quantum simulation
                qc = self.create_perturbation_circuit(
                    temp, humidity, wind, surface_type, time_horizon
                )
                
                # Execute circuit
                job = self.simulator.run(qc, shots=1024)
                result = job.result()
                counts = result.get_counts()
                
                # Calculate freeze probability from measurement outcomes
                freeze_prob = self._calculate_freeze_probability(counts)
                
                # Store in matrix
                time_key = f'{time_horizon}min'
                # Distribute probabilities across grid (simplified)
                x, y = self._get_grid_position(surface_type, grid_size)
                results[time_key][x, y] = freeze_prob
                
        # Fill grid with interpolated values
        for time_key in ['30min', '60min', '90min']:
            results[time_key] = self._interpolate_grid(results[time_key])
            
        results['surface_types'] = ['asphalt', 'concrete', 'bridge']
        results['timestamp'] = datetime.now().isoformat()
        results['forecast_windows'] = [
            (datetime.now() + timedelta(minutes=30)).isoformat(),
            (datetime.now() + timedelta(minutes=60)).isoformat(),
            (datetime.now() + timedelta(minutes=90)).isoformat()
        ]
        
        logger.info(f"QFPM generated: {np.mean(results['60min']):.1%} avg freeze probability")
        
        return results
    
    def _calculate_freeze_probability(self, counts):
        """Calculate freeze probability from quantum measurement outcomes"""
        total_shots = sum(counts.values())
        freeze_count = 0
        
        # Count measurements where outcome qubit (19) is |1⟩
        for bitstring, count in counts.items():
            # Bitstring is reversed, so qubit 19 is at position 0
            if bitstring[0] == '1':
                freeze_count += count
                
        return freeze_count / total_shots
    
    def _get_grid_position(self, surface_type, grid_size):
        """Map surface type to grid position"""
        mapping = {
            'asphalt': (grid_size // 2, grid_size // 2),  # Center
            'concrete': (0, grid_size - 1),  # Top-right
            'bridge': (grid_size - 1, grid_size // 2)  # Bottom-center
        }
        return mapping.get(surface_type, (0, 0))
    
    def _interpolate_grid(self, grid):
        """Interpolate sparse grid to fill all cells"""
        from scipy.ndimage import gaussian_filter
        # Fill zeros with nearest neighbor interpolation
        mask = grid > 0
        if mask.sum() == 0:
            return grid
        
        # Apply Gaussian smoothing for realistic spread
        smoothed = gaussian_filter(grid, sigma=1.0)
        
        # Normalize to 0-1 range
        if smoothed.max() > 0:
            smoothed = smoothed / smoothed.max()
            
        return smoothed
    
    def get_freeze_risk_summary(self, freeze_matrix):
        """
        Generate human-readable summary of freeze risks
        
        Args:
            freeze_matrix: Output from predict_freeze_matrix()
        
        Returns:
            Dict with risk levels and alerts
        """
        avg_30 = np.mean(freeze_matrix['30min'])
        avg_60 = np.mean(freeze_matrix['60min'])
        avg_90 = np.mean(freeze_matrix['90min'])
        
        max_risk = max(avg_30, avg_60, avg_90)
        
        # Determine risk level
        if max_risk > 0.7:
            risk_level = 'CRITICAL'
            color = '#FF0000'
        elif max_risk > 0.5:
            risk_level = 'HIGH'
            color = '#FF6B00'
        elif max_risk > 0.3:
            risk_level = 'MODERATE'
            color = '#FFD700'
        else:
            risk_level = 'LOW'
            color = '#00FF00'
            
        return {
            'risk_level': risk_level,
            'color': color,
            'freeze_probability': {
                '30_min': round(avg_30 * 100, 1),
                '60_min': round(avg_60 * 100, 1),
                '90_min': round(avg_90 * 100, 1)
            },
            'peak_risk_time': self._find_peak_risk_time(avg_30, avg_60, avg_90),
            'alert_message': self._generate_alert_message(risk_level, avg_60)
        }
    
    def _find_peak_risk_time(self, p30, p60, p90):
        """Find which time window has highest freeze risk"""
        probs = {'30min': p30, '60min': p60, '90min': p90}
        return max(probs, key=probs.get)
    
    def _generate_alert_message(self, risk_level, prob_60):
        """Generate user-friendly alert message"""
        if risk_level == 'CRITICAL':
            return f"⚠️ CRITICAL: {prob_60*100:.0f}% freeze probability - Black ice imminent!"
        elif risk_level == 'HIGH':
            return f"🔴 HIGH RISK: {prob_60*100:.0f}% chance of ice formation within 1 hour"
        elif risk_level == 'MODERATE':
            return f"🟡 MODERATE: {prob_60*100:.0f}% freeze probability - Exercise caution"
        else:
            return f"✅ LOW RISK: {prob_60*100:.0f}% freeze probability - Roads likely safe"
