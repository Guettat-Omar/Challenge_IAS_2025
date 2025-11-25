import pytest

from app.models.validate_payload import validate_payload


def test_validate_payload_converts_and_validates_fields():
    payload = {
        "timestamp": "2025-01-01T00:00:00Z",
        "temp": "25.5",
        "pressure": "1013.2",
        "co_mean": "12.3",
        "co_max": "15.4",
        "co_valid": 0,
        "pm2_5": "18.1",
        "pm10": "25.2",
    }

    result = validate_payload(payload)

    assert result == {
        "timestamp": "2025-01-01T00:00:00Z",
        "temp": 25.5,
        "pressure": 1013.2,
        "co_mean": 12.3,
        "co_max": 15.4,
        "co_valid": False,
        "pm2_5": 18.1,
        "pm10": 25.2,
    }


def test_validate_payload_missing_field_raises_value_error():
    payload = {
        "timestamp": "2025-01-01T00:00:00Z",
        "pressure": 1013.2,
        "co_mean": 12.3,
        "co_max": 15.4,
        "co_valid": True,
        "pm2_5": 18.1,
        "pm10": 25.2,
    }

    with pytest.raises(ValueError, match="Missing field: temp"):
        validate_payload(payload)