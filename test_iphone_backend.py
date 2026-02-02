"""
Quick iPhone Backend Test
Tests if backend is reachable from iPhone
"""

import requests
import socket
import json
from datetime import datetime

def get_local_ip():
    """Get PC's local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "Unable to detect"

def test_endpoint(url, name):
    """Test an endpoint and return status"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return f"✅ {name}: OK ({response.status_code})"
        else:
            return f"⚠️ {name}: {response.status_code}"
    except requests.ConnectionError:
        return f"❌ {name}: Cannot connect (server not running?)"
    except requests.Timeout:
        return f"❌ {name}: Timeout"
    except Exception as e:
        return f"❌ {name}: {str(e)}"

print("\n" + "="*60)
print("📱 iPhone Backend Connection Test")
print("="*60 + "\n")

# Get local IP
local_ip = get_local_ip()
print(f"🖥️  Your PC IP Address: {local_ip}")
print(f"📱 iPhone URL: http://{local_ip}:5000\n")

# Test endpoints
print("Testing Local Endpoints:")
print("-" * 60)

tests = [
    ("http://localhost:5000/api/health", "Health Check (localhost)"),
    ("http://localhost:5000/api/weather/current?lat=42.3314&lon=-83.0458", "Weather API (localhost)"),
    (f"http://{local_ip}:5000/api/health", f"Health Check ({local_ip})"),
]

for url, name in tests:
    result = test_endpoint(url, name)
    print(result)

# Railway test
print("\n" + "-" * 60)
print("Testing Railway Endpoint:")
print("-" * 60)

railway_url = "https://web-production-59bc.up.railway.app/api/health"
railway_result = test_endpoint(railway_url, "Railway Health Check")
print(railway_result)

# Summary
print("\n" + "="*60)
print("📋 Summary")
print("="*60)
print(f"\n🖥️  Local Server: http://localhost:5000")
print(f"📱 iPhone Access: http://{local_ip}:5000")
print(f"🌐 Railway: https://web-production-59bc.up.railway.app")

print("\n📝 iPhone Instructions:")
print("   1. Make sure iPhone is on SAME WiFi as this PC")
print(f"   2. Open Safari on iPhone")
print(f"   3. Go to: http://{local_ip}:5000")
print("   4. App should load!")

print("\n🔥 If local doesn't work, try Railway:")
print("   https://web-production-59bc.up.railway.app")

print("\n" + "="*60 + "\n")
