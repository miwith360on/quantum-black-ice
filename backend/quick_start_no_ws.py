"""
Quick Start Server - NO WEBSOCKET VERSION
Full weather APIs without socketio/eventlet issues
For Python 3.13 compatibility
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime
import os
from dotenv import load_dotenv

from quantum_predictor import QuantumBlackIcePredictor
from advanced_weather_calculator import AdvancedWeatherCalculator
from noaa_weather_service import NOAAWeatherService
from weather_service import WeatherService
from road_risk_analyzer import RoadRiskAnalyzer
from traffic_monitor import TrafficMonitor

# Advanced prediction systems
from quantum_freeze_matrix import QuantumFreezeProbabilityMatrix
from road_safety_mesh import RoadSafetyMeshNetwork
from bifi_calculator import BlackIceFormationIndex

# Accuracy upgrade services
from rwis_service import RWISService
from precipitation_type_service import PrecipitationTypeService
from bridge_freeze_calculator import BridgeFreezeCalculator
from overnight_cooling_predictor import OvernightCoolingPredictor
from recent_precipitation_tracker import RecentPrecipitationTracker

load_dotenv()

# Setup Flask with frontend files
static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
app = Flask(__name__, static_folder=static_folder, static_url_path='')
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize quantum services
print("\n" + "="*60)
print("🚀 QUANTUM BLACK ICE DETECTION - Starting Server")
print("="*60)

quantum_predictor = QuantumBlackIcePredictor()
weather_calculator = AdvancedWeatherCalculator()
noaa_service = NOAAWeatherService()
weather_service = WeatherService(api_key=os.getenv('OPENWEATHER_API_KEY'))
road_analyzer = RoadRiskAnalyzer()
traffic_monitor = TrafficMonitor(api_key=os.getenv('GOOGLE_MAPS_API_KEY'))

# Advanced services
qfpm = QuantumFreezeProbabilityMatrix()
mesh_network = RoadSafetyMeshNetwork()
bifi_calc = BlackIceFormationIndex()

# Accuracy upgrade services
rwis = RWISService(api_token=os.getenv('MESOWEST_API_KEY', 'demo'))
precip_type = PrecipitationTypeService()
bridge_freeze = BridgeFreezeCalculator()
overnight_cooling = OvernightCoolingPredictor()
recent_precip = RecentPrecipitationTracker()

print("✅ Quantum Predictor ready (10-qubit circuits)")
print("✅ QFPM ready (Quantum Freeze Probability Matrix)")
print("✅ IoT Mesh Network ready (Road Safety Mesh)")
print("✅ BIFI ready (Black Ice Formation Index)")
print("✅ RWIS Service ready (Road Weather Information)")
print("✅ Precipitation Type Service ready")
print("✅ Bridge Freeze Calculator ready")
print("✅ Overnight Cooling Predictor ready")
print("✅ Recent Precipitation Tracker ready")
print("✅ NOAA weather service ready")
print("✅ Advanced weather calculator ready")

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Serve mobile PWA by default"""
    response = send_from_directory(static_folder, 'mobile.html')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/mobile')
@app.route('/mobile.html')
def mobile():
    """Explicitly serve mobile interface"""
    response = send_from_directory(static_folder, 'mobile.html')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/desktop')
@app.route('/index.html')
def desktop():
    """Serve desktop interface"""
    response = send_from_directory(static_folder, 'index.html')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/route-dashboard')
@app.route('/route-dashboard.html')
def route_dashboard():
    """Serve route monitoring dashboard"""
    response = send_from_directory(static_folder, 'route-dashboard.html')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/advanced')
@app.route('/advanced-dashboard.html')
def advanced_dashboard():
    """Serve advanced dashboard"""
    response = send_from_directory(static_folder, 'advanced-dashboard.html')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/<path:path>')
def serve_static(path):
    response = send_from_directory(static_folder, path)
    # Disable caching for JavaScript and CSS files
    if path.endswith(('.js', '.css', '.html')):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

# ==================== API ENDPOINTS ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'quantum_qubits': 10,
        'service': 'Quantum Black Ice Detection (No WebSocket)',
        'features': [
            'Quantum Prediction (10-qubit)',
            'QFPM - Quantum Freeze Probability Matrix',
            'IoT Mesh Network',
            'BIFI - Black Ice Formation Index',
            'RWIS Integration',
            'Precipitation Type Detection',
            'Bridge Freeze Calculation',
            'Overnight Cooling Prediction'
        ]
    })

@app.route('/api/weather/current', methods=['GET'])
def get_current_weather():
    """Get current weather data"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if not lat or not lon:
        return jsonify({'error': 'lat and lon parameters required'}), 400
    
    try:
        # Get base weather data
        weather_data = weather_service.get_current_weather(lat, lon)
        
        # Try to enhance with NOAA data (US only)
        try:
            noaa_data = noaa_service.get_current_observations(lat, lon)
            if noaa_data:
                weather_data.update(noaa_data)
        except:
            pass
        
        # Enhance with advanced calculations
        weather_data = weather_calculator.enhance_weather_data(weather_data)
        
        return jsonify(weather_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ml/predict', methods=['POST'])
def ml_predict():
    """ML prediction endpoint"""
    try:
        data = request.get_json()
        
        # Use quantum predictor as fallback for ML
        prediction = quantum_predictor.predict(data)
        
        return jsonify({
            'success': True,
            'prediction': prediction,
            'model': 'quantum_fallback'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/quantum/predict', methods=['POST'])
def quantum_predict():
    """Quantum prediction endpoint"""
    try:
        data = request.get_json()
        weather_data = data.get('weather_data', data)
        
        prediction = quantum_predictor.predict(weather_data)
        
        return jsonify({
            'success': True,
            'quantum_prediction': prediction,
            'qubits': 10,
            'algorithm': 'QAOA'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/predictions/advanced', methods=['POST'])
def advanced_predictions():
    """Get QFPM, IoT Mesh, and BIFI predictions"""
    try:
        data = request.get_json()
        
        # QFPM prediction
        qfpm_result = qfpm.calculate_freeze_probability(
            data.get('temperature', 0),
            data.get('dew_point', 0),
            data.get('humidity', 50),
            data.get('wind_speed', 0)
        )
        
        # IoT Mesh prediction
        mesh_result = mesh_network.get_road_safety_assessment(
            data.get('lat', 0),
            data.get('lon', 0)
        )
        
        # BIFI prediction
        bifi_result = bifi_calc.calculate_bifi(
            data.get('temperature', 0),
            data.get('dew_point', 0),
            data.get('wind_speed', 0),
            data.get('precipitation', 0)
        )
        
        return jsonify({
            'success': True,
            'qfpm': qfpm_result,
            'iot_mesh': mesh_result,
            'bifi': bifi_result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/predictions/accuracy-upgrades', methods=['POST'])
def accuracy_upgrades():
    """Get accuracy upgrade predictions"""
    try:
        data = request.get_json()
        lat = data.get('lat', 0)
        lon = data.get('lon', 0)
        
        # RWIS data
        rwis_data = rwis.get_station_data(lat, lon)
        
        # Precipitation type
        precip_data = precip_type.determine_precipitation_type(
            data.get('temperature', 0),
            data.get('wet_bulb_temp', 0),
            data.get('precipitation', 0)
        )
        
        # Bridge freeze risk
        bridge_data = bridge_freeze.calculate_bridge_freeze_risk(
            data.get('air_temp', 0),
            data.get('dew_point', 0),
            data.get('wind_speed', 0)
        )
        
        # Overnight cooling
        cooling_data = overnight_cooling.predict_overnight_cooling(
            data.get('current_temp', 0),
            data.get('humidity', 50),
            data.get('cloud_cover', 50),
            data.get('wind_speed', 0)
        )
        
        # Recent precipitation
        precip_history = recent_precip.check_recent_precipitation(lat, lon)
        
        return jsonify({
            'success': True,
            'rwis': rwis_data,
            'precipitation_type': precip_data,
            'bridge_freeze': bridge_data,
            'overnight_cooling': cooling_data,
            'recent_precipitation': precip_history
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("✅ Server ready at http://localhost:5000")
    print("📱 Mobile: http://localhost:5000 (or http://192.168.1.103:5000)")
    print("💻 Desktop: http://localhost:5000/desktop")
    print("🗺️  Route Monitor: http://localhost:5000/route-dashboard")
    print("⚡ Advanced: http://localhost:5000/advanced")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
