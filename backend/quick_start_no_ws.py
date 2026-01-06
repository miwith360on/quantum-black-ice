"""
Quick Start Server - NO WEBSOCKET VERSION
Full weather APIs without socketio/eventlet issues
For Python 3.13 compatibility
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime
import os
import time
from dotenv import load_dotenv
from logging_config import setup_logging, log_api_request, log_prediction, log_error, log_performance
from prometheus_flask_exporter import PrometheusMetrics
from data_freshness import freshness_tracker
from feedback_system import feedback_system

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

# Initialize structured logging
logger = setup_logging('quick_start_no_ws')

# Setup Flask with frontend files
static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
app = Flask(__name__, static_folder=static_folder, static_url_path='')
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize Prometheus metrics
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Application info', version='1.0.0', service='quantum-black-ice')

# Initialize quantum services
logger.info("="*60)
logger.info("🚀 QUANTUM BLACK ICE DETECTION - Starting Server")
logger.info("="*60)

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

logger.info("✅ Quantum Predictor ready (10-qubit circuits)")
logger.info("✅ QFPM ready (Quantum Freeze Probability Matrix)")
logger.info("✅ IoT Mesh Network ready (Road Safety Mesh)")
logger.info("✅ BIFI ready (Black Ice Formation Index)")
logger.info("✅ RWIS Service ready (Road Weather Information)")
logger.info("✅ Precipitation Type Service ready")
logger.info("✅ Bridge Freeze Calculator ready")
logger.info("✅ Overnight Cooling Predictor ready")
logger.info("✅ Recent Precipitation Tracker ready")
logger.info("✅ NOAA weather service ready")
logger.info("✅ Advanced weather calculator ready")

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

@app.route('/validation')
@app.route('/validation-dashboard.html')
def validation_dashboard():
    """Serve validation/accuracy dashboard"""
    response = send_from_directory(static_folder, 'validation-dashboard.html')
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
    freshness_status = freshness_tracker.get_all_freshness()
    
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
        ],
        'data_freshness': freshness_status
    })

@app.route('/api/weather/current', methods=['GET'])
def get_current_weather():
    """Get current weather data"""
    start_time = time.time()
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if not lat or not lon:
        logger.warning("Weather request missing coordinates")
        return jsonify({'error': 'lat and lon parameters required'}), 400
    
    try:
        logger.debug(f"Fetching weather for lat={lat}, lon={lon}")
        
        sources_used = []
        
        # Get base weather data
        weather_data = weather_service.get_current_weather(lat, lon)
        freshness_tracker.update_timestamp('weather_api')
        sources_used.append('weather_api')
        
        # Try to enhance with NOAA data (US only)
        try:
            noaa_data = noaa_service.get_current_observations(lat, lon)
            if noaa_data:
                weather_data.update(noaa_data)
                freshness_tracker.update_timestamp('noaa')
                sources_used.append('noaa')
        except:
            pass
        
        # Enhance with advanced calculations
        weather_data = weather_calculator.enhance_weather_data(weather_data)
        
        # Add data freshness info
        freshness_info = freshness_tracker.calculate_overall_confidence(
            sources_used,
            base_confidence=0.85
        )
        weather_data['data_freshness'] = freshness_info
        
        duration_ms = (time.time() - start_time) * 1000
        log_api_request(logger, '/api/weather/current', {'lat': lat, 'lon': lon}, duration_ms)
        log_performance(logger, 'weather_fetch', duration_ms, {'source': 'openmeteo'})
        
        return jsonify(weather_data)
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_error(logger, e, {'endpoint': '/api/weather/current', 'lat': lat, 'lon': lon})
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
    start_time = time.time()
    try:
        data = request.get_json()
        weather_data = data.get('weather_data', data)
        
        logger.debug("Quantum prediction request", extra={'data': weather_data})
        
        prediction = quantum_predictor.predict(weather_data)
        freshness_tracker.update_timestamp('forecast')
        
        # Adjust confidence based on data freshness
        sources_used = ['weather_api', 'forecast']
        base_confidence = prediction.get('confidence', 0.80)
        freshness_info = freshness_tracker.calculate_overall_confidence(
            sources_used,
            base_confidence=base_confidence
        )
        
        # Update prediction with adjusted confidence
        prediction['confidence'] = freshness_info['confidence']
        prediction['data_freshness'] = freshness_info
        
        duration_ms = (time.time() - start_time) * 1000
        log_prediction(logger, 'quantum', weather_data, prediction, freshness_info['confidence'])
        log_performance(logger, 'quantum_predict', duration_ms, {'qubits': 10})
        
        return jsonify({
            'success': True,
            'quantum_prediction': prediction,
            'qubits': 10,
            'algorithm': 'QAOA'
        })
    except Exception as e:
        log_error(logger, e, {'endpoint': '/api/quantum/predict'})
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

# ==================== FEEDBACK ENDPOINTS ====================

@app.route('/api/feedback/submit', methods=['POST'])
def submit_feedback():
    """Submit ground-truth road condition report"""
    try:
        data = request.get_json()
        
        lat = data.get('lat')
        lon = data.get('lon')
        actual_condition = data.get('actual_condition')
        
        if not all([lat, lon, actual_condition]):
            return jsonify({'error': 'lat, lon, and actual_condition required'}), 400
        
        if actual_condition not in ['dry', 'wet', 'icy', 'snow']:
            return jsonify({'error': 'Invalid condition. Must be: dry, wet, icy, or snow'}), 400
        
        report = feedback_system.submit_report(
            lat=lat,
            lon=lon,
            actual_condition=actual_condition,
            predicted_condition=data.get('predicted_condition'),
            predicted_probability=data.get('predicted_probability'),
            user_comment=data.get('comment'),
            metadata=data.get('metadata')
        )
        
        logger.info(f"Feedback submitted: {actual_condition} at ({lat}, {lon})")
        
        return jsonify({
            'success': True,
            'report': report,
            'message': 'Thank you for your report!'
        })
    except Exception as e:
        log_error(logger, e, {'endpoint': '/api/feedback/submit'})
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/feedback/nearby', methods=['GET'])
def get_nearby_feedback():
    """Get recent feedback reports near a location"""
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        radius = request.args.get('radius', default=5.0, type=float)
        max_age_hours = request.args.get('max_age_hours', default=2, type=int)
        
        if not lat or not lon:
            return jsonify({'error': 'lat and lon required'}), 400
        
        reports = feedback_system.get_reports_nearby(
            lat, lon, radius, max_age_hours
        )
        
        return jsonify({
            'success': True,
            'reports': reports,
            'count': len(reports)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/feedback/vote', methods=['POST'])
def vote_feedback():
    """Upvote or downvote a feedback report"""
    try:
        data = request.get_json()
        report_id = data.get('report_id')
        vote_type = data.get('vote_type')  # 'up' or 'down'
        
        if not report_id or not vote_type:
            return jsonify({'error': 'report_id and vote_type required'}), 400
        
        success = feedback_system.vote_report(report_id, vote_type)
        
        if success:
            return jsonify({'success': True, 'message': 'Vote recorded'})
        else:
            return jsonify({'success': False, 'error': 'Report not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/feedback/stats', methods=['GET'])
def get_feedback_stats():
    """Get accuracy statistics from feedback"""
    try:
        accuracy_stats = feedback_system.get_accuracy_stats()
        recent_stats = feedback_system.get_recent_stats(hours=24)
        
        return jsonify({
            'success': True,
            'accuracy': accuracy_stats,
            'recent_24h': recent_stats
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== END FEEDBACK ENDPOINTS ====================

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
    logger.info("\n" + "="*60)
    logger.info("✅ Server ready at http://localhost:5000")
    logger.info("📱 Mobile: http://localhost:5000 (or http://192.168.1.103:5000)")
    logger.info("💻 Desktop: http://localhost:5000/desktop")
    logger.info("🗺️  Route Monitor: http://localhost:5000/route-dashboard")
    logger.info("⚡ Advanced: http://localhost:5000/advanced")
    logger.info("📊 Metrics: http://localhost:5000/metrics")
    logger.info("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
