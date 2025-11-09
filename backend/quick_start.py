"""
Quick Start Server - Quantum Only (No TensorFlow)
Fast loading for desktop testing
WITH ADVANCED FEATURES: QFPM, IoT Mesh, BIFI
Deployed on Railway - Auto-updates from GitHub
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
from datetime import datetime
import os
from dotenv import load_dotenv

from quantum_predictor import QuantumBlackIcePredictor
from advanced_weather_calculator import AdvancedWeatherCalculator
from noaa_weather_service import NOAAWeatherService
from weather_service import WeatherService

# NEW: Advanced prediction systems
from quantum_freeze_matrix import QuantumFreezeProbabilityMatrix
from road_safety_mesh import RoadSafetyMeshNetwork
from bifi_calculator import BlackIceFormationIndex

load_dotenv()

# Setup Flask with frontend files
static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
app = Flask(__name__, static_folder=static_folder, static_url_path='')
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize quantum services
quantum_predictor = QuantumBlackIcePredictor()
weather_calculator = AdvancedWeatherCalculator()
noaa_service = NOAAWeatherService()
weather_service = WeatherService(api_key=os.getenv('OPENWEATHER_API_KEY'))

# Initialize NEW advanced systems
qfpm = QuantumFreezeProbabilityMatrix(num_qubits=20)  # 20-qubit QFPM
mesh_network = RoadSafetyMeshNetwork()
bifi_calc = BlackIceFormationIndex()

print("✅ Quantum predictor initialized: 10 qubits")
print("✅ QFPM initialized: 20 qubits")
print("✅ IoT Mesh Network ready")
print("✅ BIFI Calculator ready")
print("✅ NOAA weather service ready")
print("✅ Advanced weather calculator ready")

# Serve frontend
@app.route('/')
def index():
    return send_from_directory(static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(static_folder, path)

# Health check
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'quantum_qubits': 10,
        'service': 'Quantum Black Ice Detection (Fast Mode)',
        'version': '3.0-advanced-features',
        'endpoints': [
            '/api/advanced/predict',
            '/api/bifi/calculate', 
            '/api/qfpm/predict',
            '/api/mesh/initialize'
        ]
    })

# Weather endpoint with enhancements
@app.route('/api/weather/current', methods=['GET'])
def get_current_weather():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if not lat or not lon:
        return jsonify({'error': 'Latitude and longitude required'}), 400
    
    try:
        # Try OpenWeather first (if API key exists)
        weather_data = None
        try:
            weather_data = weather_service.get_current_weather(lat, lon)
        except Exception as e:
            print(f"⚠️ OpenWeather API failed: {e}, falling back to OpenMeteo")
            # Fallback to OpenMeteo (no API key needed)
            import requests
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,wind_direction_10m"
            response = requests.get(url)
            if response.status_code == 200:
                meteo_data = response.json()['current']
                weather_data = {
                    'temperature': meteo_data['temperature_2m'],
                    'humidity': meteo_data['relative_humidity_2m'],
                    'wind_speed': meteo_data['wind_speed_10m'],
                    'wind_direction': meteo_data['wind_direction_10m'],
                    'precipitation': meteo_data['precipitation'],
                    'weather_code': meteo_data['weather_code'],
                    'location': {'lat': lat, 'lon': lon},
                    'source': 'OpenMeteo'
                }
        
        if not weather_data:
            return jsonify({'error': 'Unable to fetch weather data'}), 500
        
        # Try NOAA for US locations
        try:
            noaa_data = noaa_service.get_current_observations(lat, lon)
            if noaa_data:
                weather_data.update(noaa_data)
        except:
            pass
        
        # Enhance with calculations
        weather_data = weather_calculator.enhance_weather_data(weather_data)
        
        return jsonify(weather_data)
    except Exception as e:
        print(f"❌ Weather endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

# Quantum prediction endpoint
@app.route('/api/quantum/predict', methods=['POST'])
def quantum_predict():
    data = request.json
    
    if not data or 'weather_data' not in data:
        return jsonify({'error': 'Weather data required'}), 400
    
    try:
        weather_data = data['weather_data']
        
        # Enhance weather data
        enhanced = weather_calculator.enhance_weather_data(weather_data.copy())
        
        # Run quantum prediction
        result = quantum_predictor.predict(enhanced)
        
        return jsonify({
            'success': True,
            'quantum_prediction': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Quantum model info
@app.route('/api/quantum/model-info', methods=['GET'])
def quantum_model_info():
    return jsonify({
        'success': True,
        'model_info': {
            'name': 'Quantum Black Ice Predictor',
            'num_qubits': 10,
            'qubit_mapping': {
                '0': 'Temperature Risk',
                '1': 'Humidity/Moisture Risk',
                '2': 'Wind Chill Risk',
                '3': 'Precipitation Risk',
                '4': 'Time of Day Risk',
                '5': 'Dew Point Risk',
                '6': 'Road Surface Temperature Risk',
                '7': 'Solar Radiation Risk',
                '8': 'Visibility Risk',
                '9': 'Pressure Change Risk'
            },
            'quantum_gates': ['Hadamard', 'RY Rotation', 'CNOT', 'CZ'],
            'simulator': 'AerSimulator',
            'shots': 8192,
            'quantum_volume': 1024,
            'features': [
                'Quantum superposition for uncertainty modeling',
                'Entanglement for variable correlations',
                'Quantum interference for pattern detection',
                'Probabilistic output from quantum measurements',
                'Dew point calculation',
                'Road surface temperature estimation',
                'NOAA weather integration',
                'Enhanced accuracy with 10 qubits'
            ]
        }
    })

# Weather alerts
@app.route('/api/weather/alerts', methods=['GET'])
def get_weather_alerts():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if not lat or not lon:
        return jsonify({'error': 'Latitude and longitude required'}), 400
    
    try:
        alerts = noaa_service.get_weather_alerts(lat, lon)
        return jsonify({'alerts': alerts, 'count': len(alerts)})
    except Exception as e:
        return jsonify({'error': str(e), 'alerts': []}), 200

# ============ NEW ADVANCED ENDPOINTS ============

# QFPM - Quantum Freeze Probability Matrix
@app.route('/api/qfpm/predict', methods=['POST'])
def qfpm_predict():
    """Generate freeze probability matrix for next 30-90 minutes"""
    data = request.json
    
    if not data or 'weather_data' not in data:
        return jsonify({'error': 'Weather data required'}), 400
    
    try:
        weather_data = data['weather_data']
        grid_size = data.get('grid_size', 5)
        
        # Generate QFPM
        freeze_matrix = qfpm.predict_freeze_matrix(weather_data, grid_size)
        
        # Get summary
        summary = qfpm.get_freeze_risk_summary(freeze_matrix)
        
        return jsonify({
            'success': True,
            'freeze_matrix': {
                '30min': freeze_matrix['30min'].tolist(),
                '60min': freeze_matrix['60min'].tolist(),
                '90min': freeze_matrix['90min'].tolist(),
                'forecast_windows': freeze_matrix['forecast_windows']
            },
            'summary': summary,
            'timestamp': freeze_matrix['timestamp']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# IoT Mesh Network - Initialize sensors
@app.route('/api/mesh/initialize', methods=['POST'])
def mesh_initialize():
    """Create simulated IoT sensors around location"""
    data = request.json
    
    lat = data.get('lat')
    lon = data.get('lon')
    radius = data.get('radius_miles', 10)
    count = data.get('sensor_count', 15)
    
    if not lat or not lon:
        return jsonify({'error': 'Latitude and longitude required'}), 400
    
    try:
        sensor_ids = mesh_network.create_simulated_sensors(lat, lon, radius, count)
        return jsonify({
            'success': True,
            'sensors_created': len(sensor_ids),
            'sensor_ids': sensor_ids
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# IoT Mesh Network - Update sensor reading
@app.route('/api/mesh/sensor/update', methods=['POST'])
def mesh_sensor_update():
    """Update individual sensor reading"""
    data = request.json
    
    sensor_id = data.get('sensor_id')
    if not sensor_id:
        return jsonify({'error': 'sensor_id required'}), 400
    
    try:
        updated = mesh_network.update_sensor_reading(
            sensor_id,
            temperature=data.get('temperature'),
            friction=data.get('friction'),
            humidity=data.get('humidity'),
            surface_temp=data.get('surface_temp')
        )
        return jsonify({
            'success': True,
            'sensor': updated
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# IoT Mesh Network - Simulate all sensors
@app.route('/api/mesh/simulate', methods=['POST'])
def mesh_simulate():
    """Simulate readings for all sensors based on weather"""
    data = request.json
    
    if not data or 'weather_data' not in data:
        return jsonify({'error': 'Weather data required'}), 400
    
    try:
        weather_data = data['weather_data']
        updated_count = mesh_network.simulate_sensor_readings(weather_data)
        
        return jsonify({
            'success': True,
            'sensors_updated': updated_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# IoT Mesh Network - Get sensors in area
@app.route('/api/mesh/sensors', methods=['GET'])
def mesh_get_sensors():
    """Get all sensors within radius of location"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    radius = request.args.get('radius_miles', type=float, default=5)
    
    if not lat or not lon:
        return jsonify({'error': 'Latitude and longitude required'}), 400
    
    try:
        sensors = mesh_network.get_sensors_in_area(lat, lon, radius)
        summary = mesh_network.get_mesh_network_summary(lat, lon, radius)
        
        return jsonify({
            'success': True,
            'sensors': sensors,
            'summary': summary
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# BIFI - Calculate Black Ice Formation Index
@app.route('/api/bifi/calculate', methods=['POST'])
def bifi_calculate():
    """Calculate BIFI score for current conditions"""
    data = request.json
    
    if not data or 'weather_data' not in data:
        return jsonify({'error': 'Weather data required'}), 400
    
    try:
        weather_data = data['weather_data']
        bifi_result = bifi_calc.calculate(weather_data)
        interpretation = bifi_calc.get_bifi_interpretation(bifi_result['bifi_score'])
        
        return jsonify({
            'success': True,
            'bifi': bifi_result,
            'interpretation': interpretation
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Combined Advanced Prediction
@app.route('/api/advanced/predict', methods=['POST'])
def advanced_predict():
    """Get QFPM, IoT Mesh, and BIFI in one call"""
    data = request.json
    
    if not data or 'weather_data' not in data:
        return jsonify({'error': 'Weather data required'}), 400
    
    try:
        weather_data = data['weather_data']
        lat = data.get('lat')
        lon = data.get('lon')
        
        results = {}
        
        # Calculate BIFI
        results['bifi'] = bifi_calc.calculate(weather_data)
        results['bifi']['interpretation'] = bifi_calc.get_bifi_interpretation(results['bifi']['bifi_score'])
        
        # Generate QFPM
        freeze_matrix = qfpm.predict_freeze_matrix(weather_data)
        results['qfpm'] = {
            '30min': freeze_matrix['30min'].tolist(),
            '60min': freeze_matrix['60min'].tolist(),
            '90min': freeze_matrix['90min'].tolist(),
            'summary': qfpm.get_freeze_risk_summary(freeze_matrix)
        }
        
        # Get IoT mesh data if location provided
        if lat and lon:
            sensors = mesh_network.get_sensors_in_area(lat, lon)
            results['mesh'] = mesh_network.get_mesh_network_summary(lat, lon)
            results['mesh']['sensor_count'] = len(sensors)
        
        return jsonify({
            'success': True,
            'predictions': results,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ WEBSOCKET HANDLERS ============

@socketio.on('connect')
def handle_connect():
    print('✅ WebSocket client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('🔌 WebSocket client disconnected')

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"\n🚀 Starting Quantum Black Ice Server (Fast Mode)")
    print(f"📱 Desktop: http://localhost:{port}")
    print(f"📱 Mobile: http://localhost:{port}/mobile.html")
    print(f"⚛️ 20-Qubit QFPM System Ready!")
    print(f"🌐 IoT Mesh Network Active!")
    print(f"📊 BIFI Calculator Online!")
    print(f"📡 WebSocket: Enabled\n")
    
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
