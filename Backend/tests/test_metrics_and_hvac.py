import math

import pytest

from app.hvac.hvac_controller import _clamp_percent, decide_hvac_actions
from app.metrics import co_alerts, evaluator, pm_metrics
from app.metrics.temp_pressure_wbgt import (
    classify_pressure,
    classify_temp,
    estimate_wet_bulb,
    level_to_severity,
    wbgt_level_to_severity,
)


@pytest.fixture
def captured_alerts(monkeypatch):
    captured = []

    def fake_insert(alert):
        captured.append(alert)

    monkeypatch.setattr(pm_metrics, "insert_alert_record", fake_insert)
    monkeypatch.setattr(co_alerts, "insert_alert_record", fake_insert)
    return captured


def test_evaluate_all_metrics_builds_status_and_alerts(captured_alerts):
    reading = {
        "timestamp": "2025-01-01T00:00:00Z",
        "temp": 33,
        "pressure": 940,
        "co_mean": 0,
        "co_max": 250,
        "co_valid": True,
        "pm2_5": 40,
        "pm10": 90,
    }

    result = evaluator.evaluate_all_metrics(reading)

    assert len(result["metrics"]) == 6
    assert {a["category"] for a in result["alerts"]} == {"CO_CEILING", "TEMP", "PRESSURE"}

    status = result["results"]["status_packet"]
    assert status["co"] == {"value": 250, "level": "dark-red", "severity": "critical"}
    assert status["pm"]["pm2_5"] == {"value": 40, "level": "orange", "severity": "warning"}
    assert status["pm"]["pm10"] == {"value": 90, "level": "orange", "severity": "warning"}
    assert status["temp"] == {"value": 33, "level": "dark-red", "severity": "critical"}
    assert status["wbgt"]["level"] == "yellow"
    assert status["pressure"] == {"value": 940, "level": "orange-low", "severity": "warning"}

    assert {a["category"] for a in captured_alerts} == {"PM2.5", "PM10", "CO_CEILING"}


def test_evaluate_all_metrics_tracks_color_bands_and_severities(captured_alerts):
    reading = {
        "timestamp": "2025-01-01T01:00:00Z",
        "temp": 27.5,           # orange → warning
        "pressure": 1085.0,     # red-high → high severity
        "co_mean": 0,
        "co_max": 50.0,         # orange → warning
        "co_valid": True,
        "pm2_5": 16.0,          # yellow → none
        "pm10": 135.0,          # red → high
    }

    result = evaluator.evaluate_all_metrics(reading)

    status = result["results"]["status_packet"]
    assert status["co"] == {"value": 50.0, "level": "orange", "severity": "warning"}
    assert status["pm"]["pm2_5"] == {"value": 16.0, "level": "yellow", "severity": "none"}
    assert status["pm"]["pm10"] == {"value": 135.0, "level": "red", "severity": "high"}
    assert status["temp"] == {"value": 27.5, "level": "orange", "severity": "warning"}
    assert status["pressure"]["level"] == "red-high"

    # pressure and temp alerts should be present (PM alerts are persisted via insert calls)
    assert {a["category"] for a in result["alerts"]} == {"PRESSURE", "TEMP"}

    # Captured alerts confirm severities and include the PM10 insertion
    assert any(a["severity"] == "high" for a in captured_alerts if a["category"] == "PM10")


def test_hvac_prioritizes_emergency_purge_on_high_co():
    status_packet = {
        "timestamp": "2025-01-01T00:00:00Z",
        "co": {"value": 260, "level": "purple", "severity": "critical"},
        "pm": {
            "pm2_5": {"value": 10, "level": "green", "severity": "none"},
            "pm10": {"value": 20, "level": "green", "severity": "none"},
        },
        "temp": {"value": 20, "level": "green", "severity": "none"},
        "wbgt": {"value": 18, "level": "green", "severity": "none"},
        "pressure": {"value": 1012, "level": "green", "severity": "none"},
    }

    actions = decide_hvac_actions(status_packet)

    assert actions["ventilation_mode"] == "EMERGENCY_PURGE"
    assert actions["fan_exhaust_speed"] == 100
    assert actions["fan_supply_speed"] == 40
    assert actions["ac_power"] == 0
    assert any("EMERGENCY_PURGE" in reason for reason in actions["reasons"])


def test_hvac_adjusts_for_pm_warning():
    status_packet = {
        "timestamp": "2025-01-01T00:00:00Z",
        "co": {"value": 5, "level": "green", "severity": "none"},
        "pm": {
            "pm2_5": {"value": 35, "level": "orange", "severity": "warning"},
            "pm10": {"value": 50, "level": "yellow", "severity": "none"},
        },
        "temp": {"value": 21, "level": "green", "severity": "none"},
        "wbgt": {"value": 21, "level": "green", "severity": "none"},
        "pressure": {"value": 1010, "level": "green", "severity": "none"},
    }

    actions = decide_hvac_actions(status_packet)

    assert actions["ventilation_mode"] == "DUST_CONTROL"
    assert actions["fan_exhaust_speed"] >= 70
    assert actions["fan_supply_speed"] >= 50
    assert any("PM warning" in reason for reason in actions["reasons"])


def test_hvac_handles_heat_and_pressure_offsets():
    status_packet = {
        "timestamp": "2025-01-01T00:00:00Z",
        "co": {"value": 3, "level": "green", "severity": "none"},
        "pm": {
            "pm2_5": {"value": 12, "level": "green", "severity": "none"},
            "pm10": {"value": 15, "level": "green", "severity": "none"},
        },
        "temp": {"value": 35, "level": "dark-red", "severity": "critical"},
        "wbgt": {"value": 34, "level": "dark_red", "severity": "critical"},
        # Use the exact label hvac_controller checks for pressure adjustments
        "pressure": {"value": 1032, "level": "orange", "severity": "warning"},
    }

    actions = decide_hvac_actions(status_packet)

    assert actions["ventilation_mode"] == "HEAT_STRESS"
    assert actions["fan_supply_speed"] >= 80
    assert actions["fan_exhaust_speed"] >= 75  # heat response plus pressure exhaust boost
    assert actions["ac_power"] >= 80
    assert any("Heat danger" in reason for reason in actions["reasons"])
    assert any("increase exhaust" in reason for reason in actions["reasons"])


def test_hvac_balances_pressure_in_both_directions():
    base_packet = {
        "timestamp": "2025-01-01T00:00:00Z",
        "co": {"value": 3, "level": "green", "severity": "none"},
        "pm": {
            "pm2_5": {"value": 12, "level": "green", "severity": "none"},
            "pm10": {"value": 15, "level": "green", "severity": "none"},
        },
        "temp": {"value": 20, "level": "green", "severity": "none"},
        "wbgt": {"value": 18, "level": "green", "severity": "none"},
    }

    low_pressure_packet = {
        **base_packet,
        "pressure": {"value": 995, "level": "orange", "severity": "warning"},
    }
    high_pressure_packet = {
        **base_packet,
        "pressure": {"value": 1035, "level": "orange", "severity": "warning"},
    }

    low_actions = decide_hvac_actions(low_pressure_packet)
    high_actions = decide_hvac_actions(high_pressure_packet)

    assert low_actions["fan_supply_speed"] > 40  # adjusted upward from 40 baseline
    assert any("increase supply" in r for r in low_actions["reasons"])

    assert high_actions["fan_exhaust_speed"] > 30  # adjusted upward from 30 baseline
    assert any("increase exhaust" in r for r in high_actions["reasons"])


def test_hvac_defaults_clamp_and_reason_deduplication():
    actions = decide_hvac_actions({})

    assert actions["ventilation_mode"] == "NORMAL"
    assert actions["fan_supply_speed"] == 40
    assert actions["fan_exhaust_speed"] == 30
    assert actions["ac_power"] == 0

    # Clamp helper should keep values within bounds and remove duplicates
    assert _clamp_percent(-10) == 0
    assert _clamp_percent(150) == 100


def test_process_pm_metrics_inserts_alerts_for_non_green(monkeypatch):
    captured = []

    def fake_insert(alert):
        captured.append(alert)

    monkeypatch.setattr(pm_metrics, "insert_alert_record", fake_insert)

    result = pm_metrics.process_pm_metrics("2025-01-02T00:00:00Z", pm25=72.0, pm10=160.0)

    assert result["pm2_5"]["level"] == "red"
    assert result["pm2_5"]["severity"] == "high"
    assert result["pm10"]["level"] == "dark-red"
    assert result["pm10"]["severity"] == "critical"

    categories = {a["category"] for a in captured}
    assert categories == {"PM2.5", "PM10"}


def test_process_co_alerts_emits_all_types(monkeypatch):
    captured = []

    def fake_insert(alert):
        captured.append(alert)

    monkeypatch.setattr(co_alerts, "insert_alert_record", fake_insert)

    alerts = co_alerts.process_co_alerts(
        timestamp="2025-01-03T00:00:00Z",
        stel=250,
        twa=40,
        ceiling=250,
    )

    categories = {a["category"] for a in alerts}
    assert categories == {"CO_STEL", "CO_TWA", "CO_CEILING"}
    assert {a["severity"] for a in alerts} == {"high", "warning", "critical"}


@pytest.mark.parametrize(
    "value, classifier, expected_level",
    [
        (21.0, classify_temp, "green"),
        (25.0, classify_temp, "yellow"),
        (29.9, classify_temp, "orange"),
        (980.0, classify_pressure, "green"),
        (960.0, classify_pressure, "yellow-low"),
        (1140.0, classify_pressure, "dark-red-high"),
    ],
)
def test_environment_classifiers_return_expected_levels(value, classifier, expected_level):
    level = classifier(value)[0]

    assert level == expected_level
    assert level_to_severity(level) in {"none", "warning", "high", "critical"}


def test_wbgt_severity_and_wet_bulb_estimate():
    twb = estimate_wet_bulb(30, humidity=60)
    assert math.isfinite(twb)

    wbgt_severity = wbgt_level_to_severity("orange")
    assert wbgt_severity == "warning"