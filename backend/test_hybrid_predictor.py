from black_ice_predictor import BlackIcePredictor


def test_hybrid_predict_flags_black_ice_conditions():
    predictor = BlackIcePredictor()
    result = predictor.predict_hybrid(
        temperature=1.2,
        humidity=92,
        dew_point=0.8,
        wind_speed=1.2,
        precipitation=1.5,
        road_temperature=-0.5,
        cloud_cover=25,
        visibility=4,
        hour=2,
        recent_cooling=3.5,
        bridge_risk=1.0,
        quantum_signal=0.74,
    )

    assert result['risk_level'] in {'high', 'extreme'}
    assert result['probability'] >= 60
    assert any(f['name'] == 'Hybrid Risk Blend' for f in result['factors'])
    assert 'model' in result
