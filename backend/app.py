"""
Quantum Black Ice Detection System - Main Flask Application
Provides API endpoints for black ice prediction and monitoring
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import os
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
from advanced_weather_calculator import AdvancedWeatherCalculator
from noaa_weather_service import NOAAWeatherService
from road_risk_analyzer import RoadRiskAnalyzer
from traffic_monitor import TrafficMonitor

# Try to import flask-socketio for WebSocket support
try:
    from flask_socketio import SocketIO
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False
    print("⚠️ flask-socketio not installed - WebSocket features disabled")
    print("Install with: pip install flask-socketio python-socketio")

load_dotenv()

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
weather_calculator = AdvancedWeatherCalculator()
predictor = BlackIcePredictor()
ml_predictor = MLBlackIcePredictor()
quantum_predictor = QuantumBlackIcePredictor()
radar_service = RadarService()
db = Database()
route_monitor = RouteMonitor(weather_service, predictor)
road_analyzer = RoadRiskAnalyzer()
traffic_monitor = TrafficMonitor(api_key=os.getenv('GOOGLE_MAPS_API_KEY'))

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
    """Get AI/ML prediction using deep learning model"""
    data = request.get_json()
    
    if 'weather_sequence' not in data:
        return jsonify({'error': 'Weather sequence required'}), 400
    
    try:
        prediction = ml_predictor.predict(data['weather_sequence'])
        return jsonify(prediction)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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


# ==================== WEBSOCKET STATUS ENDPOINT ====================

@app.route('/api/websocket/status', methods=['GET'])
def websocket_status():
    """Get WebSocket connection statistics"""
    try:
        stats = ws_manager.get_connection_stats()
        return jsonify(stats)
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
    is_production = os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RENDER') or os.getenv('HEROKU')
    
    print(f"🌨️  Quantum Black Ice Detection System starting on port {port}")
    print(f"🤖 AI/ML Model: {'Loaded' if ml_predictor.is_trained else 'Not trained yet'}")
    print(f"🛰️  Radar Service: Active")
    print(f"📡 WebSocket: {'Enabled' if SOCKETIO_AVAILABLE else 'Disabled (install flask-socketio)'}")
    print(f"🗺️  Road Risk Analyzer: Active (OpenStreetMap)")
    print(f"🚦 Traffic Monitor: {'Active' if os.getenv('GOOGLE_MAPS_API_KEY') else 'Inactive (no API key)'}")
    
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
