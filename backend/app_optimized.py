"""
Quantum Black Ice Detection System - OPTIMIZED Production App
✅ Caching enabled (10min for weather data)
✅ Rate limiting (30/min for weather, 10/min for predictions)
✅ Input validation (coordinate bounds checking)
✅ Lazy service loading (avoid TensorFlow crash)
✅ Gzip compression
✅ Better error handling
✅ Enhanced health check
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_compress import Compress
from datetime import datetime, timedelta
import os
import logging
from dotenv import load_dotenv
import requests

# Core service imports (lightweight)
from weather_service import WeatherService
from black_ice_predictor import BlackIcePredictor
from database import Database
from route_monitor import RouteMonitor
from radar_service import RadarService
from websocket_server import WebSocketManager
from quantum_predictor import QuantumBlackIcePredictor
from advanced_weather_calculator import AdvancedWeatherCalculator
from noaa_weather_service import NOAAWeatherService
from road_risk_analyzer import RoadRiskAnalyzer
from traffic_monitor import TrafficMonitor
from satellite_service import SatelliteService
from openmeteo_service import OpenMeteoService
from gps_context_system import GPSContextSystem
from rwis_service import RWISService
from precipitation_type_service import PrecipitationTypeService

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== LAZY SERVICE LOADING ====================
_lazy_services = {}

def get_ml_predictor():
    """Lazy load ML predictor to avoid TensorFlow import crash"""
    if 'ml_predictor' not in _lazy_services:
        try:
            from ml_predictor import MLBlackIcePredictor
            _lazy_services['ml_predictor'] = MLBlackIcePredictor()
            logger.info("✅ ML Predictor loaded")
        except Exception as e:
            logger.warning(f"⚠️ ML Predictor unavailable: {e}")
            _lazy_services['ml_predictor'] = None
    return _lazy_services['ml_predictor']

def get_quantum_predictor_v2():
    """Lazy load 20-qubit quantum predictor"""
    if 'quantum_v2' not in _lazy_services:
        try:
            from quantum_predictor_v2 import QuantumBlackIcePredictorV2
            _lazy_services['quantum_v2'] = QuantumBlackIcePredictorV2()
            logger.info("✅ Quantum V2 loaded")
        except Exception as e:
            logger.warning(f"⚠️ Quantum V2 unavailable: {e}")
            _lazy_services['quantum_v2'] = None
    return _lazy_services['quantum_v2']

# ==================== FLASK APP CONFIGURATION ====================

is_production = os.getenv('RAILWAY_ENVIRONMENT') is not None
static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))

app = Flask(__name__, static_folder=static_folder, static_url_path='')

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": "*",  # Set to your domain in production
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"],
        "max_age": 3600
    }
})

# Initialize caching (10 minute default)
cache = Cache(app, config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 600
})

# Initialize rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Initialize compression
Compress(app)

# Initialize WebSocket support
try:
    from flask_socketio import SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    logger.info("✅ WebSocket initialized")
except ImportError:
    socketio = None
    logger.warning("⚠️ flask-socketio not available")

# ==================== SERVICE INITIALIZATION ====================

# Core services (loaded immediately)
weather_service = WeatherService(api_key=os.getenv('OPENWEATHER_API_KEY'))
noaa_service = NOAAWeatherService()
openmeteo_service = OpenMeteoService()
weather_calculator = AdvancedWeatherCalculator()
predictor = BlackIcePredictor()
quantum_predictor = QuantumBlackIcePredictor()
db = Database()
road_analyzer = RoadRiskAnalyzer()
traffic_monitor = TrafficMonitor(api_key=os.getenv('GOOGLE_MAPS_API_KEY'))
satellite_service = SatelliteService()
radar_service = RadarService()
route_monitor = RouteMonitor(weather_service, predictor)
rwis_service = RWISService()
precipitation_service = PrecipitationTypeService()
gps_context = GPSContextSystem(road_analyzer, quantum_predictor, openmeteo_service)

# WebSocket manager
ws_manager = WebSocketManager(socketio)
if socketio:
    ws_manager.initialize(app, socketio)

logger.info("✅ Core services initialized")

# ==================== UTILITY FUNCTIONS ====================

def validate_coordinates(lat, lon):
    """Validate latitude and longitude bounds"""
    try:
        lat = float(lat)
        lon = float(lon)
        if not (-90 <= lat <= 90):
            raise ValueError(f"Latitude must be between -90 and 90, got {lat}")
        if not (-180 <= lon <= 180):
            raise ValueError(f"Longitude must be between -180 and 180, got {lon}")
        return lat, lon
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid coordinates: {str(e)}")

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Serve the mobile PWA interface by default"""
    from flask import send_from_directory
    return send_from_directory(static_folder, 'mobile.html')

@app.route('/mobile')
@app.route('/mobile.html')
def mobile():
    """Explicitly serve mobile interface"""
    from flask import send_from_directory
    return send_from_directory(static_folder, 'mobile.html')

@app.route('/desktop')
@app.route('/index.html')
def desktop():
    """Serve desktop interface"""
    from flask import send_from_directory
    return send_from_directory(static_folder, 'index.html')

@app.route('/route-dashboard')
@app.route('/route-dashboard.html')
def route_dashboard():
    """Serve route monitoring dashboard"""
    from flask import send_from_directory
    return send_from_directory(static_folder, 'route-dashboard.html')

@app.route('/advanced')
@app.route('/advanced-dashboard.html')
def advanced_dashboard():
    """Serve advanced dashboard"""
    from flask import send_from_directory
    return send_from_directory(static_folder, 'advanced-dashboard.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files (CSS, JS, images, etc.)"""
    from flask import send_from_directory
    return send_from_directory(static_folder, path)

# ==================== HEALTH & STATUS ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Enhanced health check with service status"""
    services = {
        'database': 'unknown',
        'noaa_api': 'unknown',
        'openmeteo_api': 'unknown'
    }
    
    # Check database
    try:
        db._get_connection()
        services['database'] = 'healthy'
    except:
        services['database'] = 'degraded'
    
    # Check NOAA API
    try:
        response = requests.get('https://api.weather.gov', timeout=3)
        services['noaa_api'] = 'healthy' if response.status_code < 500 else 'degraded'
    except:
        services['noaa_api'] = 'degraded'
    
    # Check Open-Meteo API
    try:
        response = requests.get('https://api.open-meteo.com/v1/forecast?latitude=0&longitude=0&current_weather=true', timeout=3)
        services['openmeteo_api'] = 'healthy' if response.status_code == 200 else 'degraded'
    except:
        services['openmeteo_api'] = 'degraded'
    
    overall_status = 'healthy' if all(s == 'healthy' for s in services.values()) else 'degraded'
    
    return jsonify({
        'status': overall_status,
        'timestamp': datetime.now().isoformat(),
        'service': 'Quantum Black Ice Detection System',
        'version': '1.0.0-optimized',
        'services': services,
        'cache_enabled': True,
        'rate_limiting': True,
        'compression': True
    })

# ==================== WEATHER ENDPOINTS ====================

@app.route('/api/weather/current', methods=['GET'])
@limiter.limit("30 per minute")
@cache.cached(timeout=300, query_string=True)
def get_current_weather():
    """Get current weather with caching (5min)"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if not lat or not lon:
        return jsonify({'error': 'lat and lon required'}), 400
    
    try:
        lat, lon = validate_coordinates(lat, lon)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    try:
        weather_data = weather_service.get_current_weather(lat, lon)
        
        # Try NOAA enhancement (US only)
        try:
            noaa_data = noaa_service.get_current_observations(lat, lon)
            if noaa_data:
                weather_data.update(noaa_data)
        except:
            pass
        
        weather_data = weather_calculator.enhance_weather_data(weather_data)
        return jsonify(weather_data)
        
    except requests.Timeout:
        logger.error(f"Weather timeout for {lat},{lon}")
        return jsonify({'error': 'Weather service unavailable'}), 503
    except requests.RequestException as e:
        logger.error(f"Weather error: {e}")
        return jsonify({'error': 'Unable to fetch weather data'}), 500
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/weather/alerts', methods=['GET'])
@limiter.limit("20 per minute")
@cache.cached(timeout=300, query_string=True)
def get_weather_alerts():
    """Get weather alerts with caching"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if not lat or not lon:
        return jsonify({'error': 'lat and lon required'}), 400
    
    try:
        lat, lon = validate_coordinates(lat, lon)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    try:
        alerts = noaa_service.get_weather_alerts(lat, lon)
        return jsonify({'alerts': alerts, 'count': len(alerts)})
    except:
        return jsonify({'alerts': [], 'count': 0}), 200

@app.route('/api/weather/forecast', methods=['GET'])
@limiter.limit("20 per minute")
@cache.cached(timeout=600, query_string=True)
def get_forecast():
    """Get forecast with caching (10min)"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    hours = request.args.get('hours', default=12, type=int)
    
    if not lat or not lon:
        return jsonify({'error': 'lat and lon required'}), 400
    
    try:
        lat, lon = validate_coordinates(lat, lon)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    try:
        forecast = noaa_service.get_hourly_forecast(lat, lon, hours)
        if forecast:
            for period in forecast:
                weather_calculator.enhance_weather_data(period)
            return jsonify({'forecast': forecast, 'source': 'noaa'})
        return jsonify({'forecast': [], 'source': 'none'})
    except Exception as e:
        logger.error(f"Forecast error: {e}")
        return jsonify({'error': 'Unable to fetch forecast'}), 500

# ==================== BLACK ICE PREDICTION ====================

@app.route('/api/black-ice/predict', methods=['POST'])
@limiter.limit("10 per minute")
def predict_black_ice():
    """Predict black ice risk"""
    data = request.get_json()
    
    required = ['temperature', 'humidity', 'dew_point', 'wind_speed']
    if not all(field in data for field in required):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        prediction = predictor.predict(
            temperature=data['temperature'],
            humidity=data['humidity'],
            dew_point=data['dew_point'],
            wind_speed=data['wind_speed'],
            precipitation=data.get('precipitation', 0),
            road_temperature=data.get('road_temperature')
        )
        
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
        logger.error(f"Prediction error: {e}")
        return jsonify({'error': 'Prediction failed'}), 500

@app.route('/api/black-ice/monitor', methods=['GET'])
@limiter.limit("20 per minute")
@cache.cached(timeout=300, query_string=True)
def monitor_location():
    """Monitor location for black ice"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if not lat or not lon:
        return jsonify({'error': 'lat and lon required'}), 400
    
    try:
        lat, lon = validate_coordinates(lat, lon)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    
    try:
        weather_data = weather_service.get_current_weather(lat, lon)
        
        prediction = predictor.predict(
            temperature=weather_data['temperature'],
            humidity=weather_data['humidity'],
            dew_point=weather_data['dew_point'],
            wind_speed=weather_data['wind_speed'],
            precipitation=weather_data.get('precipitation', 0)
        )
        
        history = db.get_location_history(lat, lon, hours=24)
        
        return jsonify({
            'location': {'lat': lat, 'lon': lon},
            'weather': weather_data,
            'prediction': prediction,
            'history': history
        })
    except Exception as e:
        logger.error(f"Monitor error: {e}")
        return jsonify({'error': 'Monitoring failed'}), 500

# ==================== QUANTUM PREDICTIONS ====================

@app.route('/api/quantum/predict', methods=['POST'])
@limiter.limit("10 per minute")
def quantum_predict():
    """Quantum black ice prediction"""
    data = request.get_json()
    
    try:
        lat = data.get('lat')
        lon = data.get('lon')
        
        if lat and lon:
            lat, lon = validate_coordinates(lat, lon)
            weather_data = openmeteo_service.get_current_weather(lat, lon)
        else:
            weather_data = data.get('weather_data', {})
        
        result = quantum_predictor.predict(weather_data)
        return jsonify({
            'success': True,
            'quantum_prediction': result
        })
    except Exception as e:
        logger.error(f"Quantum prediction error: {e}")
        return jsonify({'error': 'Quantum prediction failed'}), 500

@app.route('/api/quantum/v2/predict', methods=['POST'])
@limiter.limit("5 per minute")
def quantum_v2_predict():
    """20-qubit quantum prediction (lazy loaded)"""
    quantum_v2 = get_quantum_predictor_v2()
    
    if not quantum_v2:
        return jsonify({'error': 'Quantum V2 unavailable'}), 503
    
    data = request.get_json()
    
    try:
        lat = data.get('lat')
        lon = data.get('lon')
        
        if lat and lon:
            lat, lon = validate_coordinates(lat, lon)
            weather_data = openmeteo_service.get_current_weather(lat, lon)
        else:
            weather_data = data.get('weather_data', {})
        
        location_context = data.get('location_context', {})
        result = quantum_v2.predict(weather_data, location_context)
        
        return jsonify({
            'success': True,
            'quantum_v2_prediction': result
        })
    except Exception as e:
        logger.error(f"Quantum V2 error: {e}")
        return jsonify({'error': 'Quantum V2 prediction failed'}), 500

# ==================== ML PREDICTIONS (LAZY LOADED) ====================

@app.route('/api/ml/predict', methods=['POST'])
@limiter.limit("10 per minute")
def ml_predict():
    """ML prediction (lazy loaded to avoid TensorFlow crash)"""
    ml_predictor = get_ml_predictor()
    
    if not ml_predictor:
        return jsonify({'error': 'ML predictor unavailable'}), 503
    
    try:
        data = request.get_json(force=True)
        
        temp = float(data.get("temperature") or data.get("temp") or 32.0)
        humidity = float(data.get("humidity") or 50.0)
        dew_point = float(data.get("dew_point") or data.get("dewpoint") or 30.0)
        wind_speed = float(data.get("wind_speed") or data.get("wind") or 5.0)
        precipitation = float(data.get("precipitation") or data.get("precip") or 0.0)
        
        weather_data = {
            "temperature": temp,
            "humidity": humidity,
            "dew_point": dew_point,
            "wind_speed": wind_speed,
            "precipitation": precipitation
        }
        
        prediction = ml_predictor.predict(weather_data)
        return jsonify({
            'success': True,
            'ml_prediction': prediction
        })
    except Exception as e:
        logger.error(f"ML prediction error: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== ROUTE MONITORING ====================

@app.route('/api/route/analyze', methods=['POST'])
@limiter.limit("10 per minute")
def analyze_route():
    """Analyze route for black ice risk"""
    data = request.get_json()
    
    if 'waypoints' not in data or len(data['waypoints']) < 2:
        return jsonify({'error': 'At least 2 waypoints required'}), 400
    
    try:
        analysis = route_monitor.analyze_route(data['waypoints'])
        db.store_route_analysis(analysis)
        return jsonify(analysis)
    except Exception as e:
        logger.error(f"Route analysis error: {e}")
        return jsonify({'error': 'Route analysis failed'}), 500

# ==================== SERVER STARTUP ====================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    
    print("\n" + "="*80)
    print("🚀 QUANTUM BLACK ICE DETECTION SYSTEM - OPTIMIZED VERSION")
    print("="*80)
    print(f"✅ Caching: Enabled (10min default)")
    print(f"✅ Rate Limiting: 30/min weather, 10/min predictions")
    print(f"✅ Compression: Gzip enabled")
    print(f"✅ Input Validation: Coordinate bounds checking")
    print(f"✅ Lazy Loading: Heavy services loaded on-demand")
    print(f"✅ Error Handling: Specific exceptions with logging")
    print("="*80)
    print(f"🌐 Server starting on http://0.0.0.0:{port}")
    print("="*80 + "\n")
    
    if socketio:
        socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
    else:
        app.run(host='0.0.0.0', port=port, debug=False)
