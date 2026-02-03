import sys
sys.path.insert(0, 'backend')
from bifi_calculator_v3 import MLEnhancedBIFI

bifi = MLEnhancedBIFI()
print('✅ BIFI v3 ML-Enhanced loaded')
print(f'Training samples: {len(bifi.accuracy_history)}')

# Test calculation
result = bifi.calculate({
    'temperature': 30,
    'humidity': 85,
    'wind_speed': 10,
    'precipitation': 0.5
})

print(f'\n📊 Test Result:')
print(f'BIFI Score: {result["bifi_score"]}')
print(f'Risk Level: {result["risk_level"]}')
print(f'Confidence: {result["confidence"]}%')
print(f'\n{result["explanation"]}')
