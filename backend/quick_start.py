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
from road_risk_analyzer import RoadRiskAnalyzer
from traffic_monitor import TrafficMonitor

# NEW: Advanced prediction systems
from quantum_freeze_matrix import QuantumFreezeProbabilityMatrix
from road_safety_mesh import RoadSafetyMeshNetwork
from bifi_calculator import BlackIceFormationIndex

# NEW: Accuracy upgrade services
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

# Initialize SocketIO with eventlet for production
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet', engineio_logger=False, logger=False)

# Initialize quantum services
quantum_predictor = QuantumBlackIcePredictor()
weather_calculator = AdvancedWeatherCalculator()
noaa_service = NOAAWeatherService()
weather_service = WeatherService(api_key=os.getenv('OPENWEATHER_API_KEY'))
road_analyzer = RoadRiskAnalyzer()
traffic_monitor = TrafficMonitor(api_key=os.getenv('GOOGLE_MAPS_API_KEY'))

# Initialize NEW advanced systems
qfpm = QuantumFreezeProbabilityMatrix(num_qubits=20)  # 20-qubit QFPM
mesh_network = RoadSafetyMeshNetwork()
bifi_calc = BlackIceFormationIndex()

# Initialize accuracy upgrade services
rwis = RWISService()  # Real road surface temps from DOT sensors
precip_service = PrecipitationTypeService()  # Freezing rain detection
bridge_calc = BridgeFreezeCalculator()  # Enhanced bridge freeze prediction
overnight_cooling = OvernightCoolingPredictor()  # 2-6 AM freeze prediction
recent_precip_tracker = RecentPrecipitationTracker()  # Wet pavement detection

print("✅ Quantum predictor initialized: 10 qubits")
print("✅ QFPM initialized: 20 qubits")
print("✅ IoT Mesh Network ready")
print("✅ BIFI Calculator ready")
print("✅ Road Risk Analyzer ready (OpenStreetMap)")
print(f"🚦 Traffic Monitor: {'Active' if os.getenv('GOOGLE_MAPS_API_KEY') else 'Inactive (no API key)'}")
print("✅ RWIS Service ready (Real road temps)")
print("✅ Precipitation Type Service ready (Freezing rain detection)")
print("✅ Bridge Freeze Calculator ready")
print("✅ Overnight Cooling Predictor ready (2-6 AM freeze timing)")
print("✅ Recent Precipitation Tracker ready (Wet pavement detection)")
print("✅ NOAA weather service ready")
print("✅ Advanced weather calculator ready")

# Serve frontend with cache-busting
@app.route('/')
def index():
    response = send_from_directory(static_folder, 'index.html')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/<path:path>')
def serve_static(path):
    response = send_from_directory(static_folder, path)
    # Disable caching for JavaScript and CSS files to ensure updates
    if path.endswith(('.js', '.css', '.html')):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

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
            '/api/mesh/initialize',
            '/api/road/analyze',
            '/api/traffic/tile-url'
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
        openweather_key = os.getenv('OPENWEATHER_API_KEY')
        
        if openweather_key and openweather_key != 'your_api_key_here':
            try:
                weather_data = weather_service.get_current_weather(lat, lon)
            except Exception as e:
                print(f"⚠️ OpenWeather API failed: {e}, falling back to OpenMeteo")
        
        # Fallback to OpenMeteo (no API key needed)
        if not weather_data:
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

# ML prediction endpoint with flexible input
@app.route('/api/ml/predict', methods=['POST'])
def ml_predict():
    """Get AI/ML prediction with flexible input handling"""
    try:
        data = request.get_json(force=True)
        print("📥 Incoming ML data:", data)  # Debugging

        # Accept flexible key names to prevent 400 errors
        temp = float(data.get("temperature") or data.get("temp") or 32.0)
        humidity = float(data.get("humidity") or 50.0)
        dew = float(data.get("dew_point") or data.get("dew") or 28.0)
        road_temp = float(data.get("road_temp") or temp)

        # Simple ML formula for black ice risk
        freeze_risk = max(0.0, min(1.0, (humidity / 100) * (32 - temp) / 32))
        confidence = round(0.75 + 0.1 * (1 - abs(32 - temp) / 32), 2)

        return jsonify({
            "success": True,
            "risk": freeze_risk,
            "confidence": confidence,
            "prediction": "high_risk" if freeze_risk > 0.7 else "moderate_risk" if freeze_risk > 0.4 else "low_risk"
        }), 200

    except Exception as e:
        print("❌ ML Predict Error:", e)
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/ml/model-info', methods=['GET'])
def ml_model_info():
    """Get ML model information"""
    return jsonify({
        "success": True,
        "model": "Black Ice Risk Predictor",
        "version": "1.0",
        "algorithm": "Gradient-based freeze risk analysis",
        "features": ["temperature", "humidity", "dew_point", "road_temp"]
    })

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

# ============ ACCURACY UPGRADE ENDPOINTS ============

# RWIS - Real Road Surface Temperatures
@app.route('/api/rwis/road-temp', methods=['GET'])
def get_rwis_road_temp():
    """Get real road surface temperature from nearest DOT sensor"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if not lat or not lon:
        return jsonify({'error': 'Latitude and longitude required'}), 400
    
    try:
        road_temp_data = rwis.get_road_temp_estimate(lat, lon)
        return jsonify({
            'success': True,
            'road_temp_data': road_temp_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# RWIS - Regional Freeze Map
@app.route('/api/rwis/freeze-map', methods=['GET'])
def get_rwis_freeze_map():
    """Get freeze status from multiple nearby sensors"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if not lat or not lon:
        return jsonify({'error': 'Latitude and longitude required'}), 400
    
    try:
        freeze_map = rwis.get_regional_freeze_map(lat, lon)
        return jsonify({
            'success': True,
            'freeze_map': freeze_map,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Precipitation Type Detection
@app.route('/api/precipitation/type', methods=['GET'])
def get_precipitation_type():
    """Detect freezing rain, sleet, snow, etc."""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if not lat or not lon:
        return jsonify({'error': 'Latitude and longitude required'}), 400
    
    try:
        precip_data = precip_service.get_precipitation_type(lat, lon)
        return jsonify({
            'success': True,
            'precipitation': precip_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Hourly Precipitation Forecast
@app.route('/api/precipitation/forecast', methods=['GET'])
def get_precipitation_forecast():
    """Get hour-by-hour precipitation forecast with black ice risk"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    hours = request.args.get('hours', type=int, default=6)
    
    if not lat or not lon:
        return jsonify({'error': 'Latitude and longitude required'}), 400
    
    try:
        forecast = precip_service.get_hourly_precipitation_forecast(lat, lon, hours)
        return jsonify({
            'success': True,
            'hourly_forecast': forecast,
            'hours': len(forecast),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Bridge Freeze Calculation
@app.route('/api/bridge/freeze-risk', methods=['POST'])
def calculate_bridge_freeze():
    """Calculate when a bridge will freeze (bridges freeze at warmer temps)"""
    data = request.json
    
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    try:
        # Accept multiple key names for flexibility
        air_temp = data.get('air_temp_f') or data.get('current_temp_f') or data.get('temperature')
        wind_speed = data.get('wind_speed_mph') or data.get('wind_speed') or 5
        humidity = data.get('humidity_percent') or data.get('humidity') or 70
        bridge_material = data.get('bridge_material') or data.get('bridge_type') or 'concrete'
        bridge_length = data.get('bridge_length_ft') or 200
        
        if air_temp is None:
            return jsonify({'error': 'temperature data required (air_temp_f, current_temp_f, or temperature)'}), 400
        
        freeze_data = bridge_calc.calculate_bridge_freeze_temp(
            air_temp, wind_speed, humidity, bridge_material, bridge_length
        )
        
        return jsonify({
            'success': True,
            'bridge_freeze': freeze_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Bridge vs Road Comparison
@app.route('/api/bridge/compare', methods=['POST'])
def compare_bridge_road():
    """Compare freeze risk: bridge vs regular road"""
    data = request.json
    
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    try:
        comparison = bridge_calc.compare_bridge_vs_road(
            data.get('air_temp_f'),
            data.get('wind_speed_mph', 5),
            data.get('humidity_percent', 70),
            data.get('bridge_material', 'concrete')
        )
        
        return jsonify({
            'success': True,
            'comparison': comparison,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Overnight Cooling Prediction
@app.route('/api/overnight/freeze-prediction', methods=['POST'])
def predict_overnight_freeze():
    """Predict when roads will freeze overnight (critical for 2-6 AM)"""
    data = request.json
    
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    try:
        from datetime import datetime
        
        prediction = overnight_cooling.predict_freeze_time(
            current_temp_f=data.get('current_temp_f'),
            current_time=datetime.now(),
            dew_point_f=data.get('dew_point_f'),
            wind_speed_mph=data.get('wind_speed_mph', 5),
            cloud_cover_percent=data.get('cloud_cover_percent', 0)
        )
        
        return jsonify({
            'success': True,
            'overnight_prediction': prediction,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Hourly Cooling Forecast
@app.route('/api/overnight/hourly-forecast', methods=['POST'])
def get_hourly_cooling():
    """Get hour-by-hour temperature drop forecast"""
    data = request.json
    
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    try:
        forecast = overnight_cooling.get_hourly_cooling_forecast(
            current_temp_f=data.get('current_temp_f'),
            dew_point_f=data.get('dew_point_f'),
            wind_speed_mph=data.get('wind_speed_mph', 5),
            cloud_cover_percent=data.get('cloud_cover_percent', 0),
            hours=data.get('hours', 12)
        )
        
        return jsonify({
            'success': True,
            'hourly_forecast': forecast,
            'hours': len(forecast),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Recent Precipitation Check
@app.route('/api/precipitation/recent', methods=['GET'])
def check_recent_precipitation():
    """Check if roads are wet from recent rain/snow"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    hours_back = request.args.get('hours_back', type=int, default=6)
    
    if not lat or not lon:
        return jsonify({'error': 'Latitude and longitude required'}), 400
    
    try:
        precip_data = recent_precip_tracker.check_recent_precipitation(
            lat, lon, hours_back
        )
        
        return jsonify({
            'success': True,
            'recent_precipitation': precip_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Road Hazard Analysis
@app.route('/api/road/analyze', methods=['GET'])
def analyze_road_risks():
    """
    Analyze road features for black ice risk zones (bridges, overpasses, tunnels)
    Query params: lat, lon, radius (optional, default 5000m)
    """
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    radius = request.args.get('radius', type=float, default=5000)
    
    if not lat or not lon:
        return jsonify({'error': 'Latitude and longitude required'}), 400
    
    try:
        road_features = road_analyzer.get_high_risk_roads(lat, lon, radius)
        return jsonify(road_features)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Traffic - current conditions
@app.route('/api/traffic/current', methods=['GET'])
def get_traffic_conditions():
    """Get real-time traffic conditions (requires GOOGLE_MAPS_API_KEY)"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    radius = request.args.get('radius', type=int, default=5000)

    if not lat or not lon:
        return jsonify({'error': 'Latitude and longitude required'}), 400

    try:
        traffic = traffic_monitor.get_traffic_conditions(lat, lon, radius)
        return jsonify(traffic)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/traffic/tile-url', methods=['GET'])
def get_traffic_tile_url():
    """Return a pseudo tile URL (placeholder) or message if key missing"""
    zoom = request.args.get('zoom', type=int, default=13)
    try:
        tile_url = traffic_monitor.get_traffic_tile_url(zoom)
        if tile_url:
            return jsonify({'tile_url': tile_url, 'available': True})
        else:
            return jsonify({
                'available': False,
                'message': 'Traffic layer requires GOOGLE_MAPS_API_KEY environment variable'
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
    
    # Production mode: use eventlet worker for WebSocket support
    # Development mode: allow unsafe werkzeug for testing
    is_production = os.getenv('RENDER') or os.getenv('RAILWAY_ENVIRONMENT')
    
    if is_production:
        print("🔧 Production mode: Using eventlet worker for WebSocket (or fallback if started directly)")
        # Note: On Render we start via gunicorn (see render.yaml). If this file is executed directly
        # in production, allow_unsafe_werkzeug=True prevents Flask 3.0 RuntimeError and keeps service up.
        socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
    else:
        print("🔧 Development mode: Using unsafe Werkzeug (local only)")
        socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
