"""
Quick Start Server - Quantum Only (No TensorFlow)
Fast loading for desktop testing
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

load_dotenv()

# Setup Flask with frontend files
static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
app = Flask(__name__, static_folder=static_folder, static_url_path='')
CORS(app)

# Initialize quantum services only
quantum_predictor = QuantumBlackIcePredictor()
weather_calculator = AdvancedWeatherCalculator()
noaa_service = NOAAWeatherService()
weather_service = WeatherService(api_key=os.getenv('OPENWEATHER_API_KEY'))

print("✅ Quantum predictor initialized: 10 qubits")
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
        'service': 'Quantum Black Ice Detection (Fast Mode)'
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

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"\n🚀 Starting Quantum Black Ice Server (Fast Mode)")
    print(f"📱 Desktop: http://localhost:{port}")
    print(f"📱 Mobile: http://localhost:{port}/mobile.html")
    print(f"⚛️ 10-Qubit Quantum System Ready!\n")
    
    app.run(host='0.0.0.0', port=port, debug=False)
