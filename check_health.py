"""
Comprehensive Health Check for Quantum Black Ice Detection System
Checks all APIs, services, and system components
"""

import sys
import os
from datetime import datetime

# Test imports
print("=" * 80)
print("QUANTUM BLACK ICE SYSTEM - HEALTH CHECK")
print("=" * 80)
print(f"Timestamp: {datetime.now().isoformat()}")
print(f"Python Version: {sys.version}")
print()

# Track health status
health_status = {
    'imports': {},
    'apis': {},
    'services': {},
    'overall': 'UNKNOWN'
}

# 1. Check Core Imports
print("\n[1/5] CHECKING CORE DEPENDENCIES...")
print("-" * 80)

dependencies = [
    ('Flask', 'flask'),
    ('Flask-CORS', 'flask_cors'),
    ('Requests', 'requests'),
    ('NumPy', 'numpy'),
    ('Pandas', 'pandas'),
    ('Scikit-learn', 'sklearn'),
    ('TensorFlow', 'tensorflow'),
    ('Qiskit', 'qiskit'),
    ('Python-dotenv', 'dotenv'),
]

for name, module in dependencies:
    try:
        __import__(module)
        print(f"✅ {name:20} - Installed")
        health_status['imports'][name] = 'OK'
    except ImportError as e:
        print(f"❌ {name:20} - NOT FOUND ({str(e)})")
        health_status['imports'][name] = 'MISSING'

# 2. Check Backend Services
print("\n[2/5] CHECKING BACKEND SERVICES...")
print("-" * 80)

backend_modules = [
    'weather_service',
    'noaa_weather_service',
    'openmeteo_service',
    'black_ice_predictor',
    'quantum_predictor',
    'quantum_predictor_v2',
    'rwis_service',
    'precipitation_type_service',
    'ml_road_temp_model',
    'iot_sensor_network',
    'accident_predictor',
    'bifi_calculator',
    'quantum_freeze_matrix',
]

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

for module in backend_modules:
    try:
        __import__(module)
        print(f"✅ {module:30} - OK")
        health_status['services'][module] = 'OK'
    except Exception as e:
        print(f"⚠️  {module:30} - ERROR: {str(e)[:50]}")
        health_status['services'][module] = f'ERROR: {str(e)[:50]}'

# 3. Check External APIs
print("\n[3/5] CHECKING EXTERNAL APIs...")
print("-" * 80)

import requests

apis_to_test = [
    {
        'name': 'NOAA Weather.gov',
        'url': 'https://api.weather.gov/points/42.52,-83.10',
        'timeout': 10
    },
    {
        'name': 'Open-Meteo',
        'url': 'https://api.open-meteo.com/v1/forecast?latitude=42.52&longitude=-83.10&current_weather=true',
        'timeout': 10
    },
    {
        'name': 'MesoWest RWIS (Demo)',
        'url': 'https://api.synopticdata.com/v2/stations/latest?token=demotoken&radius=42.52,-83.10,25&network=1',
        'timeout': 10
    },
]

for api in apis_to_test:
    try:
        response = requests.get(api['url'], timeout=api['timeout'])
        if response.status_code == 200:
            print(f"✅ {api['name']:25} - Status {response.status_code} - OK")
            health_status['apis'][api['name']] = 'OK'
        else:
            print(f"⚠️  {api['name']:25} - Status {response.status_code}")
            health_status['apis'][api['name']] = f'HTTP {response.status_code}'
    except requests.exceptions.Timeout:
        print(f"⚠️  {api['name']:25} - TIMEOUT")
        health_status['apis'][api['name']] = 'TIMEOUT'
    except Exception as e:
        print(f"❌ {api['name']:25} - ERROR: {str(e)[:40]}")
        health_status['apis'][api['name']] = f'ERROR: {str(e)[:40]}'

# 4. Check Flask App (without running server)
print("\n[4/5] CHECKING FLASK APPLICATION...")
print("-" * 80)

try:
    from backend.simple_server import app as simple_app
    print(f"✅ Simple Server (Flask)     - OK")
    health_status['services']['flask_simple'] = 'OK'
except Exception as e:
    print(f"❌ Simple Server (Flask)     - ERROR: {str(e)[:50]}")
    health_status['services']['flask_simple'] = f'ERROR: {str(e)[:50]}'

# 5. Generate Report
print("\n[5/5] HEALTH SUMMARY")
print("=" * 80)

# Count statuses
import_ok = sum(1 for v in health_status['imports'].values() if v == 'OK')
import_total = len(health_status['imports'])
service_ok = sum(1 for v in health_status['services'].values() if v == 'OK')
service_total = len(health_status['services'])
api_ok = sum(1 for v in health_status['apis'].values() if v == 'OK')
api_total = len(health_status['apis'])

print(f"\n📦 Dependencies:  {import_ok}/{import_total} OK")
print(f"⚙️  Services:      {service_ok}/{service_total} OK")
print(f"🌐 External APIs: {api_ok}/{api_total} OK")

# Overall health
if import_ok == import_total and api_ok >= api_total - 1:
    health_status['overall'] = 'HEALTHY'
    print(f"\n✅ OVERALL STATUS: {health_status['overall']}")
elif import_ok >= import_total - 2:
    health_status['overall'] = 'DEGRADED'
    print(f"\n⚠️  OVERALL STATUS: {health_status['overall']}")
else:
    health_status['overall'] = 'CRITICAL'
    print(f"\n❌ OVERALL STATUS: {health_status['overall']}")

# Issues found
print("\n📋 ISSUES DETECTED:")
issues = []

for category, items in [('Imports', health_status['imports']), 
                        ('Services', health_status['services']), 
                        ('APIs', health_status['apis'])]:
    for name, status in items.items():
        if status != 'OK':
            issues.append(f"  • {category} - {name}: {status}")

if issues:
    for issue in issues:
        print(issue)
else:
    print("  None - All systems operational!")

# Recommendations
print("\n💡 RECOMMENDATIONS:")
if health_status['imports'].get('TensorFlow') != 'OK':
    print("  • TensorFlow issue detected - Use simple_server.py instead of app.py")
    print("    Command: python backend/simple_server.py")
if health_status['apis'].get('MesoWest RWIS (Demo)') != 'OK':
    print("  • MesoWest API issue - System will use fallback data sources")

print("\n" + "=" * 80)
print("Health check complete!")
print("=" * 80)
