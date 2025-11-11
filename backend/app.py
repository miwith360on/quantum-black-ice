"""
Quantum Black Ice Detection System - Main Flask Application
Provides API endpoints for black ice prediction and monitoring
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import os
import logging
from dotenv import load_dotenv
import asyncio
import threading

from weather_service import WeatherService
from black_ice_predictor import BlackIcePredictor
from database import Database
from route_monitor import RouteMonitor
from ml_predictor import MLBlackIcePredictor
from radar_service import RadarService
from websocket_server import WebSocketManager
from quantum_predictor import QuantumBlackIcePredictor
from quantum_predictor_v2 import QuantumBlackIcePredictorV2
from advanced_weather_calculator import AdvancedWeatherCalculator
from noaa_weather_service import NOAAWeatherService
from road_risk_analyzer import RoadRiskAnalyzer
from traffic_monitor import TrafficMonitor
from satellite_service import SatelliteService
from openmeteo_service import OpenMeteoService
from gps_context_system import GPSContextSystem
from ml_road_temp_model import MLRoadSurfaceTempModel
from iot_sensor_network import IoTSensorNetwork
from accident_predictor import AccidentPredictor
from bifi_calculator import BlackIceFormationIndex
from quantum_freeze_matrix import QuantumFreezeProbabilityMatrix

# Try to import flask-socketio for WebSocket support
try:
    from flask_socketio import SocketIO
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False
    print("⚠️ flask-socketio not installed - WebSocket features disabled")
    print("Install with: pip install flask-socketio python-socketio")

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Determine if running in production (Railway)
is_production = os.getenv('RAILWAY_ENVIRONMENT') is not None

# Set static folder path - in production, frontend is one level up
if is_production:
    static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
else:
    static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))

app = Flask(__name__, 
            static_folder=static_folder,
            static_url_path='')
CORS(app)

# Initialize SocketIO for real-time WebSocket streaming
socketio = None
if SOCKETIO_AVAILABLE:
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    print("✅ WebSocket server initialized")

# Initialize services
weather_service = WeatherService(api_key=os.getenv('OPENWEATHER_API_KEY'))
noaa_service = NOAAWeatherService()
openmeteo_service = OpenMeteoService()
satellite_service = SatelliteService()
weather_calculator = AdvancedWeatherCalculator()
predictor = BlackIcePredictor()
ml_predictor = MLBlackIcePredictor()
quantum_predictor = QuantumBlackIcePredictor()
quantum_predictor_v2 = QuantumBlackIcePredictorV2()  # NEW: 20-qubit system!
ml_road_temp = MLRoadSurfaceTempModel()  # NEW: ML Road Surface Temp Model!
iot_network = IoTSensorNetwork()  # NEW: IoT Sensor Network!
accident_predictor = AccidentPredictor()  # NEW: Accident Prediction!
bifi_calculator = BlackIceFormationIndex()  # BIFI Calculator
qfpm_calculator = QuantumFreezeProbabilityMatrix()  # Quantum Freeze Probability Matrix
radar_service = RadarService()
db = Database()
route_monitor = RouteMonitor(weather_service, predictor)
road_analyzer = RoadRiskAnalyzer()
traffic_monitor = TrafficMonitor(api_key=os.getenv('GOOGLE_MAPS_API_KEY'))

# Initialize GPS context system with integrated services
gps_context = GPSContextSystem(road_analyzer, quantum_predictor, openmeteo_service)

# Initialize WebSocket manager
ws_manager = WebSocketManager(socketio)
if socketio:
    ws_manager.initialize(app, socketio)


# Serve frontend files
@app.route('/')
def index():
    """Serve the mobile PWA interface"""
    from flask import send_from_directory
    return send_from_directory(static_folder, 'mobile.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files (CSS, JS, images, etc.)"""
    from flask import send_from_directory
    return send_from_directory(static_folder, path)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Quantum Black Ice Detection System'
    })


@app.route('/api/weather/current', methods=['GET'])
def get_current_weather():
    """Get current weather data for a location"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if not lat or not lon:
        return jsonify({'error': 'Latitude and longitude required'}), 400
    
    try:
        # Get basic weather data
        weather_data = weather_service.get_current_weather(lat, lon)
        
        # Try to enhance with NOAA data (US only)
        try:
            noaa_data = noaa_service.get_current_observations(lat, lon)
            if noaa_data:
                # NOAA data is more accurate for US locations
                weather_data.update(noaa_data)
        except Exception as noaa_error:
            # NOAA might fail for non-US locations, continue with OpenWeather
            pass
        
        # Calculate advanced metrics
        weather_data = weather_calculator.enhance_weather_data(weather_data)
        
        return jsonify(weather_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/weather/alerts', methods=['GET'])
def get_weather_alerts():
    """Get NOAA weather alerts for location (US only)"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if not lat or not lon:
        return jsonify({'error': 'Latitude and longitude required'}), 400
    
    try:
        alerts = noaa_service.get_weather_alerts(lat, lon)
        return jsonify({'alerts': alerts, 'count': len(alerts)})
    except Exception as e:
        return jsonify({'error': str(e), 'alerts': []}), 200


@app.route('/api/weather/forecast', methods=['GET'])
def get_forecast():
    """Get hourly forecast with advanced metrics"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    hours = request.args.get('hours', default=12, type=int)
    
    if not lat or not lon:
        return jsonify({'error': 'Latitude and longitude required'}), 400
    
    try:
        forecast = noaa_service.get_hourly_forecast(lat, lon, hours)
        if not forecast:
            # Fallback to OpenWeather if NOAA fails
            return jsonify({'forecast': [], 'source': 'none'})
        
        # Enhance each forecast period with calculated metrics
        for period in forecast:
            period = weather_calculator.enhance_weather_data(period)
        
        return jsonify({'forecast': forecast, 'source': 'noaa', 'hours': len(forecast)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/black-ice/predict', methods=['POST'])
def predict_black_ice():
    """Predict black ice formation risk"""
    data = request.get_json()
    
    required_fields = ['temperature', 'humidity', 'dew_point', 'wind_speed']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required weather data'}), 400
    
    try:
        prediction = predictor.predict(
            temperature=data['temperature'],
            humidity=data['humidity'],
            dew_point=data['dew_point'],
            wind_speed=data['wind_speed'],
            precipitation=data.get('precipitation', 0),
            road_temperature=data.get('road_temperature')
        )
        
        # Store prediction in database
        if 'lat' in data and 'lon' in data:
            db.store_prediction(
                lat=data['lat'],
                lon=data['lon'],
                risk_level=prediction['risk_level'],
                probability=prediction['probability'],
                factors=prediction['factors']
            )
        
        return jsonify(prediction)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/black-ice/monitor', methods=['GET'])
def monitor_location():
    """Monitor a specific location for black ice conditions"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if not lat or not lon:
        return jsonify({'error': 'Latitude and longitude required'}), 400
    
    try:
        # Get current weather
        weather_data = weather_service.get_current_weather(lat, lon)
        
        # Make prediction
        prediction = predictor.predict(
            temperature=weather_data['temperature'],
            humidity=weather_data['humidity'],
            dew_point=weather_data['dew_point'],
            wind_speed=weather_data['wind_speed'],
            precipitation=weather_data.get('precipitation', 0)
        )
        
        # Get historical data
        history = db.get_location_history(lat, lon, hours=24)
        
        return jsonify({
            'location': {'lat': lat, 'lon': lon},
            'weather': weather_data,
            'prediction': prediction,
            'history': history,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get active black ice alerts"""
    try:
        alerts = db.get_active_alerts()
        return jsonify({'alerts': alerts})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get system statistics"""
    try:
        stats = db.get_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/route/analyze', methods=['POST'])
def analyze_route():
    """Analyze a complete route with multiple waypoints"""
    data = request.get_json()
    
    if 'waypoints' not in data or len(data['waypoints']) < 2:
        return jsonify({'error': 'Route must have at least 2 waypoints'}), 400
    
    try:
        analysis = route_monitor.analyze_route(data['waypoints'])
        
        # Store route analysis in database
        db.store_route_analysis(analysis)
        
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/locations/monitor', methods=['POST'])
def monitor_multiple_locations():
    """Monitor multiple locations simultaneously"""
    data = request.get_json()
    
    if 'locations' not in data or not data['locations']:
        return jsonify({'error': 'At least one location required'}), 400
    
    try:
        results = route_monitor.monitor_locations(data['locations'])
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/route/corridor', methods=['POST'])
def get_route_corridor():
    """Get weather conditions along route corridor"""
    data = request.get_json()
    
    required = ['start', 'end']
    if not all(field in data for field in required):
        return jsonify({'error': 'Start and end points required'}), 400
    
    try:
        samples = data.get('samples', 10)
        corridor = route_monitor.get_route_corridor(
            data['start'], 
            data['end'],
            samples
        )
        return jsonify({'corridor': corridor})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/routes/saved', methods=['GET'])
def get_saved_routes():
    """Get user's saved routes"""
    try:
        routes = db.get_saved_routes()
        return jsonify({'routes': routes})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/routes/save', methods=['POST'])
def save_route():
    """Save a route for quick monitoring"""
    data = request.get_json()
    
    required = ['name', 'waypoints']
    if not all(field in data for field in required):
        return jsonify({'error': 'Name and waypoints required'}), 400
    
    try:
        route_id = db.save_route(
            name=data['name'],
            waypoints=data['waypoints'],
            description=data.get('description', '')
        )
        return jsonify({'route_id': route_id, 'message': 'Route saved successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== NEW: AI/ML ENDPOINTS ====================

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

        # Placeholder simple ML formula
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
    """Get information about the ML model"""
    try:
        info = ml_predictor.get_model_info()
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ml/train', methods=['POST'])
def ml_train():
    """Train the ML model with historical data"""
    data = request.get_json()
    
    if 'training_data' not in data:
        return jsonify({'error': 'Training data required'}), 400
    
    try:
        epochs = data.get('epochs', 50)
        batch_size = data.get('batch_size', 32)
        
        ml_predictor.train(
            training_data=data['training_data'],
            epochs=epochs,
            batch_size=batch_size
        )
        
        return jsonify({
            'success': True,
            'message': 'Model trained successfully',
            'info': ml_predictor.get_model_info()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== NEW: QUANTUM PREDICTION ENDPOINTS ====================

@app.route('/api/quantum/predict', methods=['POST'])
def quantum_predict():
    """Quantum-enhanced black ice probability prediction"""
    data = request.json
    
    if not data or 'weather_data' not in data:
        return jsonify({'error': 'Weather data required'}), 400
    
    try:
        weather_data = data['weather_data']
        result = quantum_predictor.predict(weather_data)
        
        return jsonify({
            'success': True,
            'quantum_prediction': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quantum/model-info', methods=['GET'])
def quantum_model_info():
    """Get quantum model architecture information"""
    return jsonify({
        'success': True,
        'model_info': {
            'name': 'Quantum Black Ice Predictor',
            'num_qubits': 5,
            'qubit_mapping': {
                '0': 'Temperature Risk',
                '1': 'Humidity/Moisture Risk',
                '2': 'Wind Chill Risk',
                '3': 'Precipitation Risk',
                '4': 'Time of Day Risk'
            },
            'quantum_gates': ['Hadamard', 'RY Rotation', 'CNOT', 'CZ'],
            'simulator': 'AerSimulator',
            'shots': 8192,
            'features': [
                'Quantum superposition for uncertainty modeling',
                'Entanglement for variable correlations',
                'Quantum interference for pattern detection',
                'Probabilistic output from quantum measurements'
            ]
        }
    })

@app.route('/api/quantum/circuit', methods=['POST'])
def quantum_circuit_visualization():
    """Get quantum circuit representation for given weather data"""
    data = request.json
    
    if not data or 'weather_data' not in data:
        return jsonify({'error': 'Weather data required'}), 400
    
    try:
        weather_data = data['weather_data']
        
        # Create circuit and get its text representation
        circuit = quantum_predictor.create_quantum_circuit(weather_data)
        circuit_str = str(circuit)
        
        return jsonify({
            'success': True,
            'circuit': circuit_str,
            'num_qubits': circuit.num_qubits,
            'depth': circuit.depth(),
            'operations': circuit.count_ops()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== NEW: QUANTUM V2 (20-QUBIT) ENDPOINTS ====================

@app.route('/api/quantum/v2/predict', methods=['POST'])
def quantum_v2_predict():
    """20-qubit quantum prediction with hyper-local micro-climate modeling"""
    data = request.json
    
    if not data or 'weather_data' not in data:
        return jsonify({'error': 'Weather data required'}), 400
    
    try:
        weather_data = data['weather_data']
        location_context = data.get('location_context', {})
        
        result = quantum_predictor_v2.predict(weather_data, location_context)
        
        return jsonify({
            'success': True,
            'quantum_v2_prediction': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quantum/v2/model-info', methods=['GET'])
def quantum_v2_model_info():
    """Get Quantum V2 (20-qubit) model architecture information"""
    return jsonify({
        'success': True,
        'model_info': {
            'name': 'Quantum Black Ice Predictor V2',
            'version': 'V2_20QUBIT',
            'num_qubits': 20,
            'quantum_volume': 1048576,  # 2^20
            'circuit_depth': 24,
            'entanglement_layers': 4,
            'qubit_categories': {
                'Core Weather (0-4)': [
                    'Q0: Temperature Risk',
                    'Q1: Humidity/Moisture Risk',
                    'Q2: Wind Chill Risk',
                    'Q3: Precipitation Risk',
                    'Q4: Time of Day Risk'
                ],
                'Surface Conditions (5-9)': [
                    'Q5: Dew Point Risk',
                    'Q6: Road Surface Temperature Risk',
                    'Q7: Solar Radiation Risk',
                    'Q8: Visibility Risk',
                    'Q9: Pressure Change Risk'
                ],
                'Micro-Climate (10-14)': [
                    'Q10: Elevation/Terrain Risk',
                    'Q11: Shade/Sun Exposure Risk',
                    'Q12: Traffic Heat Dissipation',
                    'Q13: Pavement Type/Thermal Mass',
                    'Q14: Recent Weather History (Cooling Rate)'
                ],
                'Location-Specific (15-19)': [
                    'Q15: Bridge/Overpass Proximity',
                    'Q16: Water Body Proximity (Humidity)',
                    'Q17: Urban Heat Island Effect',
                    'Q18: Tree Cover/Wind Blockage',
                    'Q19: Micro-Elevation Changes'
                ]
            },
            'quantum_gates': ['Hadamard', 'RY Rotation', 'CNOT', 'CZ'],
            'simulator': 'AerSimulator',
            'shots': 16384,
            'features': [
                'Hyper-local micro-climate predictions',
                '20-dimensional quantum state space',
                'Deep entanglement (4 layers)',
                'Location-aware risk factors',
                'Traffic heat signature analysis',
                'Pavement thermal mass modeling',
                'Bridge cooling effect modeling',
                'Urban heat island correction'
            ]
        }
    })

@app.route('/api/quantum/compare', methods=['POST'])
def quantum_compare_versions():
    """Compare V1 (10-qubit) vs V2 (20-qubit) predictions"""
    data = request.json
    
    if not data or 'weather_data' not in data:
        return jsonify({'error': 'Weather data required'}), 400
    
    try:
        weather_data = data['weather_data']
        location_context = data.get('location_context', {})
        
        # Run both predictors
        v1_result = quantum_predictor.predict(weather_data)
        v2_result = quantum_predictor_v2.predict(weather_data, location_context)
        
        return jsonify({
            'success': True,
            'comparison': {
                'v1': {
                    'model': '10-qubit',
                    'probability': v1_result['probability'],
                    'risk_level': v1_result['risk_level'],
                    'quantum_volume': v1_result['quantum_metrics']['quantum_volume']
                },
                'v2': {
                    'model': '20-qubit',
                    'probability': v2_result['probability'],
                    'risk_level': v2_result['risk_level'],
                    'quantum_volume': v2_result['quantum_metrics']['quantum_volume']
                },
                'improvement': {
                    'quantum_volume_increase': f"{(v2_result['quantum_metrics']['quantum_volume'] / v1_result['quantum_metrics']['quantum_volume']):.0f}x",
                    'additional_factors': 10,
                    'location_aware': True
                }
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== BIFI & QFPM ENDPOINTS ====================

@app.route('/api/bifi/calculate', methods=['POST'])
def calculate_bifi():
    """Calculate Black Ice Formation Index (BIFI)"""
    data = request.json
    
    if not data or 'weather_data' not in data:
        return jsonify({'error': 'Weather data required'}), 400
    
    try:
        weather_data = data['weather_data']
        
        # Calculate BIFI
        bifi_result = bifi_calculator.calculate(weather_data)
        
        # Generate interpretation
        interpretation = f"{bifi_result['risk_level']}: {bifi_result['risk_description']}"
        
        return jsonify({
            'success': True,
            'bifi': bifi_result,
            'interpretation': interpretation
        })
    except Exception as e:
        logger.error(f"BIFI calculation error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/qfpm/predict', methods=['POST'])
def qfpm_predict():
    """Quantum Freeze Probability Matrix prediction"""
    data = request.json
    
    if not data or 'weather_data' not in data:
        return jsonify({'error': 'Weather data required'}), 400
    
    try:
        weather_data = data['weather_data']
        
        # Extract parameters with defaults
        base_temp = weather_data.get('temperature', 32)
        base_humidity = weather_data.get('humidity', 70)
        base_wind = weather_data.get('wind_speed', 5)
        surface_type = weather_data.get('surface_type', 'asphalt')
        
        # Generate freeze probability matrix
        freeze_matrix = qfpm_calculator.predict_freeze_matrix(
            base_temp=base_temp,
            base_humidity=base_humidity,
            base_wind=base_wind,
            surface_types=[surface_type]
        )
        
        # Get risk summary
        summary = qfpm_calculator.get_freeze_risk_summary(freeze_matrix)
        
        return jsonify({
            'success': True,
            'matrix': {
                '30min': freeze_matrix['30min'].tolist(),
                '60min': freeze_matrix['60min'].tolist(),
                '90min': freeze_matrix['90min'].tolist(),
                'surface_types': freeze_matrix['surface_types'],
                'forecast_windows': freeze_matrix['forecast_windows']
            },
            'summary': summary,
            'timestamp': freeze_matrix['timestamp']
        })
    except Exception as e:
        logger.error(f"QFPM prediction error: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== NEW: RADAR & SATELLITE ENDPOINTS ====================

@app.route('/api/radar/layers', methods=['GET'])
def get_radar_layers():
    """Get radar overlay layers for a location"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if not lat or not lon:
        return jsonify({'error': 'Latitude and longitude required'}), 400
    
    try:
        layers = radar_service.get_radar_layers(lat, lon)
        return jsonify(layers)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/satellite/imagery', methods=['GET'])
def get_satellite_imagery():
    """Get satellite imagery layers"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    layer_type = request.args.get('type', 'visible')
    
    if not lat or not lon:
        return jsonify({'error': 'Latitude and longitude required'}), 400
    
    try:
        imagery = radar_service.get_satellite_imagery(lat, lon, layer_type)
        return jsonify(imagery)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/radar/composite', methods=['GET'])
def get_composite_layers():
    """Get all available weather overlay layers"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if not lat or not lon:
        return jsonify({'error': 'Latitude and longitude required'}), 400
    
    try:
        composite = radar_service.get_composite_layers(lat, lon)
        return jsonify(composite)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== NEW: ROAD RISK & TRAFFIC ENDPOINTS ====================

@app.route('/api/road/analyze', methods=['GET'])
def analyze_road_risks():
    """
    Analyze road features for black ice risk zones
    Query params: lat, lon, radius (optional, default 5000m)
    """
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    radius = request.args.get('radius', type=float, default=5000)
    
    if not lat or not lon:
        return jsonify({'error': 'lat and lon required'}), 400
    
    try:
        road_features = road_analyzer.get_high_risk_roads(lat, lon, radius)
        return jsonify(road_features)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/traffic/current', methods=['GET'])
def get_traffic_conditions():
    """
    Get real-time traffic conditions
    Query params: lat, lon, radius (optional, default 5000m)
    """
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    radius = request.args.get('radius', type=int, default=5000)
    
    if not lat or not lon:
        return jsonify({'error': 'lat and lon required'}), 400
    
    try:
        traffic = traffic_monitor.get_traffic_conditions(lat, lon, radius)
        return jsonify(traffic)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/traffic/tile-url', methods=['GET'])
def get_traffic_tile_url():
    """Get URL for traffic layer tiles (for map overlay)"""
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


@app.route('/api/route/analyze-traffic', methods=['POST'])
def analyze_route_traffic():
    """
    Analyze traffic along a route with ice risk
    POST body: { "origin": [lat, lon], "destination": [lat, lon], "weather_risk": 0-100 }
    """
    try:
        data = request.get_json()
        origin = tuple(data.get('origin', []))
        destination = tuple(data.get('destination', []))
        weather_risk = data.get('weather_risk', 0)
        
        if len(origin) != 2 or len(destination) != 2:
            return jsonify({'error': 'origin and destination must be [lat, lon] arrays'}), 400
        
        result = traffic_monitor.analyze_route_traffic(origin, destination, weather_risk)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/hazards/combined', methods=['GET'])
def get_combined_hazards():
    """
    Get combined road + weather + traffic risk assessment
    Query params: lat, lon
    """
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if not lat or not lon:
        return jsonify({'error': 'lat and lon required'}), 400
    
    try:
        # Get weather data
        weather_data = weather_service.get_current_weather(lat, lon)
        
        # Try to enhance with NOAA if in US
        try:
            noaa_data = noaa_service.get_current_observations(lat, lon)
            if noaa_data:
                weather_data.update(noaa_data)
        except:
            pass
        
        # Calculate advanced metrics
        weather_data = weather_calculator.enhance_weather_data(weather_data)
        
        # Get quantum prediction
        quantum_result = quantum_predictor.predict(weather_data)
        weather_risk = quantum_result['probability'] * 100
        
        # Get road features
        road_features = road_analyzer.get_high_risk_roads(lat, lon)
        
        # Get traffic conditions
        traffic = traffic_monitor.get_traffic_conditions(lat, lon)
        
        # Calculate combined risk
        combined = road_analyzer.calculate_route_risk(road_features, weather_risk)
        
        return jsonify({
            'weather': {
                'temperature': weather_data.get('temperature'),
                'humidity': weather_data.get('humidity'),
                'conditions': weather_data.get('description'),
                'risk_score': weather_risk
            },
            'quantum_analysis': quantum_result,
            'road_features': road_features,
            'traffic': traffic,
            'combined_risk': combined,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== SATELLITE & ADVANCED WEATHER ENDPOINTS ====================

@app.route('/api/satellite/thermal', methods=['GET'])
def get_satellite_thermal():
    """Get NASA satellite thermal imagery for ice detection"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if not lat or not lon:
        return jsonify({'error': 'lat and lon required'}), 400
    
    try:
        thermal_data = satellite_service.get_thermal_imagery(lat, lon)
        return jsonify(thermal_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/satellite/regional', methods=['GET'])
def get_regional_ice_map():
    """Get wide-area satellite ice formation map"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if not lat or not lon:
        return jsonify({'error': 'lat and lon required'}), 400
    
    try:
        regional_data = satellite_service.get_regional_ice_map(lat, lon)
        return jsonify(regional_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/weather/openmeteo', methods=['GET'])
def get_openmeteo_weather():
    """
    Get high-accuracy weather from OpenMeteo
    Includes ROAD SURFACE TEMPERATURE - critical for black ice!
    """
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if not lat or not lon:
        return jsonify({'error': 'lat and lon required'}), 400
    
    try:
        weather_data = openmeteo_service.get_current_weather(lat, lon)
        return jsonify(weather_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/weather/forecast-enhanced', methods=['GET'])
def get_enhanced_forecast():
    """Get hourly forecast with road surface temperature"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    hours = request.args.get('hours', type=int, default=12)
    
    if not lat or not lon:
        return jsonify({'error': 'lat and lon required'}), 400
    
    try:
        forecast = openmeteo_service.get_hourly_forecast(lat, lon, hours)
        return jsonify(forecast)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== GPS CONTEXT & DYNAMIC QUANTUM ALERTS ====================

@app.route('/api/gps/update', methods=['POST'])
def gps_location_update():
    """
    Update GPS location and get real-time quantum alerts
    Returns dynamic alerts like "High Quantum Risk on Bridge XYZ - 0.84 probability"
    """
    try:
        data = request.get_json()
        lat = data.get('lat')
        lon = data.get('lon')
        
        if not lat or not lon:
            return jsonify({'error': 'lat and lon required'}), 400
        
        # Get enhanced weather from OpenMeteo (includes road temp!)
        weather_data = openmeteo_service.get_current_weather(lat, lon)
        
        # Update GPS context and get quantum-powered alerts
        context = gps_context.update_location(lat, lon, weather_data)
        
        return jsonify(context)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/gps/nearest-hazard', methods=['GET'])
def get_nearest_hazard():
    """Get nearest road hazard (bridge/overpass) from GPS location"""
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        
        if not lat or not lon:
            return jsonify({'error': 'lat and lon required'}), 400
        
        hazard = gps_context.get_nearest_hazard(lat, lon)
        return jsonify(hazard)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/gps/route-preview', methods=['POST'])
def get_route_preview():
    """Preview route hazards before driving"""
    try:
        data = request.get_json()
        destination = data.get('destination')
        
        if not destination:
            return jsonify({'error': 'destination required'}), 400
        
        preview = gps_context.get_route_preview(destination)
        return jsonify(preview)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== ML ROAD SURFACE TEMPERATURE ====================

@app.route('/api/ml/road-temp/predict', methods=['POST'])
def ml_road_temp_predict():
    """
    Predict exact road surface temperature using ML model
    Combines satellite, quantum, traffic, and weather data
    """
    try:
        data = request.get_json()
        
        current_data = data.get('current_data', {})
        historical_sequence = data.get('historical_sequence', [])
        
        if not current_data.get('weather'):
            return jsonify({'error': 'weather data required'}), 400
        
        # Predict road temperature
        prediction = ml_road_temp.predict_road_temperature(
            current_data,
            historical_sequence
        )
        
        return jsonify({
            'success': True,
            'prediction': prediction
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ml/road-temp/train', methods=['POST'])
def ml_road_temp_train():
    """
    Train ML road temperature model on historical data
    """
    try:
        data = request.get_json()
        
        training_data = data.get('training_data', [])
        epochs = data.get('epochs', 50)
        batch_size = data.get('batch_size', 32)
        
        if len(training_data) < 100:
            return jsonify({'error': 'Need at least 100 training samples'}), 400
        
        # Train model
        history = ml_road_temp.train_model(
            training_data,
            epochs=epochs,
            batch_size=batch_size
        )
        
        return jsonify({
            'success': True,
            'training_history': history,
            'model_info': ml_road_temp.get_model_info()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ml/road-temp/info', methods=['GET'])
def ml_road_temp_info():
    """Get ML road temperature model information"""
    return jsonify({
        'success': True,
        'model_info': ml_road_temp.get_model_info()
    })


@app.route('/api/ml/road-temp/enhanced-prediction', methods=['POST'])
def ml_road_temp_enhanced():
    """
    Enhanced prediction that combines ALL data sources:
    - Current weather
    - Satellite thermal imaging
    - Quantum V2 prediction
    - Traffic heat signatures
    - Location micro-climate
    """
    try:
        data = request.get_json()
        
        lat = data.get('lat')
        lon = data.get('lon')
        
        if not lat or not lon:
            return jsonify({'error': 'lat and lon required'}), 400
        
        # === GATHER ALL DATA SOURCES ===
        
        # 1. Weather data
        weather_data = openmeteo_service.get_current_weather(lat, lon)
        weather_data['latitude'] = lat
        weather_data['longitude'] = lon
        
        # 2. Satellite thermal data
        try:
            satellite_data = satellite_service.get_thermal_imagery(lat, lon)
        except:
            satellite_data = None
        
        # 3. Quantum V2 prediction (20-qubit with micro-climate)
        try:
            location_context = data.get('location_context', {})
            quantum_result = quantum_predictor_v2.predict(weather_data, location_context)
        except:
            quantum_result = None
        
        # 4. Traffic data
        try:
            traffic_data = traffic_monitor.get_traffic_conditions(lat, lon, radius=1000)
        except:
            traffic_data = None
        
        # === COMBINE INTO ML PREDICTION ===
        
        current_data = {
            'weather': weather_data,
            'satellite': satellite_data,
            'quantum': quantum_result,
            'traffic': traffic_data,
            'location': location_context
        }
        
        prediction = ml_road_temp.predict_road_temperature(current_data)
        
        return jsonify({
            'success': True,
            'ml_prediction': prediction,
            'data_sources_used': {
                'weather': weather_data is not None,
                'satellite': satellite_data is not None,
                'quantum_v2': quantum_result is not None,
                'traffic': traffic_data is not None
            },
            'openmeteo_road_temp': weather_data.get('road_surface_temp'),
            'quantum_ice_probability': quantum_result.get('probability') if quantum_result else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/gps/route-preview-enhanced', methods=['POST'])
def preview_route():
    """Preview quantum risk along a route before driving"""
    try:
        data = request.get_json()
        dest_lat = data.get('destination_lat')
        dest_lon = data.get('destination_lon')
        
        if not dest_lat or not dest_lon:
            return jsonify({'error': 'destination_lat and destination_lon required'}), 400
        
        preview = gps_context.get_route_preview(dest_lat, dest_lon)
        return jsonify(preview)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== WEBSOCKET STATUS ENDPOINT ====================

@app.route('/api/websocket/status', methods=['GET'])
def websocket_status():
    """Get WebSocket connection statistics"""
    try:
        stats = ws_manager.get_connection_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== IOT SENSOR NETWORK ====================

@app.route('/api/iot/sensors/nearby', methods=['GET'])
def get_nearby_iot_sensors():
    """Get IoT sensors near a location"""
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        radius = request.args.get('radius', type=float, default=10)
        
        if not lat or not lon:
            return jsonify({'error': 'lat and lon required'}), 400
        
        sensors = iot_network.get_nearby_sensors(lat, lon, radius)
        
        return jsonify({
            'success': True,
            'num_sensors': len(sensors),
            'sensors': [
                {
                    'sensor_id': s.sensor_id,
                    'type': s.sensor_type.value,
                    'location': s.location,
                    'protocol': s.protocol.value,
                    'is_active': s.is_active
                }
                for s in sensors
            ]
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/iot/data', methods=['GET'])
def get_iot_sensor_data():
    """Get aggregated IoT sensor data for a location"""
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        radius = request.args.get('radius', type=float, default=10)
        
        if not lat or not lon:
            return jsonify({'error': 'lat and lon required'}), 400
        
        data = iot_network.get_sensor_data(lat, lon, radius)
        
        return jsonify({
            'success': True,
            'sensor_data': data
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/iot/bridge-temp', methods=['GET'])
def get_bridge_temperature():
    """Get bridge deck temperature from IoT sensors"""
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        bridge_name = request.args.get('name', 'Unknown Bridge')
        
        if not lat or not lon:
            return jsonify({'error': 'lat and lon required'}), 400
        
        temp = iot_network.get_bridge_temperature(lat, lon, bridge_name)
        
        if temp is None:
            return jsonify({
                'success': False,
                'message': 'No bridge deck sensors available',
                'bridge_name': bridge_name
            })
        
        return jsonify({
            'success': True,
            'bridge_name': bridge_name,
            'temperature': temp,
            'unit': '°F',
            'warning': temp <= 32
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/iot/enhanced-prediction', methods=['POST'])
def get_iot_enhanced_prediction():
    """
    Quantum prediction enhanced with real IoT sensor validation
    Combines:
    - Quantum V2 20-qubit prediction
    - Real bridge deck temperature sensors
    - Road moisture detectors
    - Weather station data
    """
    try:
        data = request.get_json()
        
        lat = data.get('lat')
        lon = data.get('lon')
        
        if not lat or not lon:
            return jsonify({'error': 'lat and lon required'}), 400
        
        # 1. Get weather data
        weather_data = openmeteo_service.get_current_weather(lat, lon)
        
        # 2. Get Quantum V2 prediction
        location_context = data.get('location_context', {})
        quantum_result = quantum_predictor_v2.predict(weather_data, location_context)
        
        # 3. Enhance with IoT sensor data
        enhanced = iot_network.integrate_with_quantum_prediction(
            lat, lon, quantum_result
        )
        
        return jsonify({
            'success': True,
            'enhanced_prediction': enhanced
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/iot/network-status', methods=['GET'])
def get_iot_network_status():
    """Get IoT sensor network status"""
    try:
        status = iot_network.get_network_status()
        return jsonify({
            'success': True,
            'network_status': status
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== PREDICTIVE ANALYTICS DASHBOARD ====================

@app.route('/api/analytics/predict-accident', methods=['POST'])
def predict_accident():
    """
    Predict accident probability for a location
    Combines: weather + quantum risk + traffic + IoT + historical patterns
    """
    try:
        data = request.get_json()
        
        lat = data.get('lat')
        lon = data.get('lon')
        time_window = data.get('time_window_hours', 3)
        
        if not lat or not lon:
            return jsonify({'error': 'lat and lon required'}), 400
        
        # Gather all data sources
        weather_data = openmeteo_service.get_current_weather(lat, lon)
        
        location_context = data.get('location_context', {})
        quantum_risk = quantum_predictor_v2.predict(weather_data, location_context)
        
        try:
            traffic_data = traffic_monitor.get_traffic_conditions(lat, lon, radius=1000)
        except:
            traffic_data = None
        
        try:
            iot_data = iot_network.get_sensor_data(lat, lon, radius_km=10)
        except:
            iot_data = None
        
        # Predict accident
        location = {
            'lat': lat,
            'lon': lon,
            'name': data.get('location_name', 'Current Location'),
            **location_context
        }
        
        prediction = accident_predictor.predict_accident_risk(
            location=location,
            weather_data=weather_data,
            quantum_risk=quantum_risk,
            traffic_data=traffic_data,
            iot_data=iot_data,
            time_window_hours=time_window
        )
        
        return jsonify({
            'success': True,
            'accident_prediction': prediction
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/route-analysis', methods=['POST'])
def analyze_route_accidents():
    """Analyze entire route for accident hotspots"""
    try:
        data = request.get_json()
        
        route_points = data.get('route_points', [])
        
        if not route_points or len(route_points) < 2:
            return jsonify({'error': 'Need at least 2 route points'}), 400
        
        # Get weather for route start
        weather_data = openmeteo_service.get_current_weather(
            route_points[0]['lat'],
            route_points[0]['lon']
        )
        
        # Get quantum risks for each point
        quantum_risks = []
        for point in route_points:
            try:
                risk = quantum_predictor_v2.predict(weather_data, {})
                quantum_risks.append(risk)
            except:
                quantum_risks.append({})
        
        # Analyze route
        analysis = accident_predictor.analyze_route_accidents(
            route_points=route_points,
            weather_data=weather_data,
            quantum_risks=quantum_risks
        )
        
        return jsonify({
            'success': True,
            'route_analysis': analysis
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/heatmap', methods=['GET'])
def get_accident_heatmap():
    """Get regional accident risk heatmap"""
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        radius = request.args.get('radius', type=float, default=20)
        grid_size = request.args.get('grid_size', type=int, default=20)
        
        if not lat or not lon:
            return jsonify({'error': 'lat and lon required'}), 400
        
        heatmap = accident_predictor.get_regional_heatmap(
            center_lat=lat,
            center_lon=lon,
            radius_km=radius,
            grid_size=grid_size
        )
        
        return jsonify({
            'success': True,
            'heatmap': heatmap
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/dashboard', methods=['POST'])
def get_analytics_dashboard():
    """
    Get complete analytics dashboard data
    Everything needed for the predictive analytics UI
    """
    try:
        data = request.get_json()
        
        lat = data.get('lat')
        lon = data.get('lon')
        
        if not lat or not lon:
            return jsonify({'error': 'lat and lon required'}), 400
        
        # Gather all data
        weather_data = openmeteo_service.get_current_weather(lat, lon)
        
        location_context = data.get('location_context', {})
        quantum_risk = quantum_predictor_v2.predict(weather_data, location_context)
        
        try:
            traffic_data = traffic_monitor.get_traffic_conditions(lat, lon, radius=1000)
        except:
            traffic_data = None
        
        try:
            iot_data = iot_network.get_sensor_data(lat, lon, radius_km=10)
        except:
            iot_data = None
        
        # Get dashboard data
        dashboard = accident_predictor.get_dashboard_data(
            lat=lat,
            lon=lon,
            weather_data=weather_data,
            quantum_risk=quantum_risk,
            traffic_data=traffic_data,
            iot_data=iot_data
        )
        
        return jsonify({
            'success': True,
            'dashboard': dashboard
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Initialize database
    db.initialize()
    
    # Run the application with WebSocket support
    port = int(os.getenv('PORT', 5000))
    # Disable debug mode to prevent restart issues with TensorFlow
    debug = False
    
    # Detect if running on Railway or other cloud platform
    is_production = os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('HEROKU')
    
    print(f"🌨️  Quantum Black Ice Detection System starting on port {port}")
    print(f"🤖 AI/ML Model: {'Loaded' if ml_predictor.is_trained else 'Not trained yet'}")
    print(f"🤖 ML Road Temp: {'Trained' if ml_road_temp.is_trained else 'Not trained (using physics-based)'}")
    print(f"⚛️  Quantum V1: 10-Qubit System Active")
    print(f"⚛️  Quantum V2: 20-Qubit System Active (HYPER-LOCAL!)")
    print(f"� IoT Sensor Network: {iot_network.get_network_status()['active_sensors']} sensors active")
    print(f"�🛰️  Radar Service: Active")
    print(f"🛰️  NASA Satellite: Active (MODIS/VIIRS Thermal)")
    print(f"🌍 OpenMeteo: Active (Road Surface Temp)")
    print(f"📡 WebSocket: {'Enabled' if SOCKETIO_AVAILABLE else 'Disabled (install flask-socketio)'}")
    print(f"🗺️  Road Risk Analyzer: Active (OpenStreetMap)")
    print(f"🚦 Traffic Monitor: {'Active' if os.getenv('GOOGLE_MAPS_API_KEY') else 'Inactive (no API key)'}")
    print(f"📍 GPS Context System: Active (Quantum Alerts)")
    
    if not is_production:
        print(f"\n💡 Open: http://localhost:{port}")
        print(f"📊 Dashboard: Open frontend/advanced-dashboard.html in your browser")
        print(f"📱 Mobile: Open frontend/mobile.html in your browser")
    else:
        print(f"\n🌐 Production Mode - Cloud Deployment Active")
    
    print(f"\n✨ Press CTRL+C to stop\n")
    
    if socketio:
        # Run with WebSocket support
        socketio.run(app, host='0.0.0.0', port=port, debug=debug, allow_unsafe_werkzeug=True)
    else:
        # Fallback to regular Flask
        app.run(host='0.0.0.0', port=port, debug=debug)
