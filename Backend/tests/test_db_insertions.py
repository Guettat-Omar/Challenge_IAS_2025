import json
import sqlite3

import pytest

import app.db.alerts_db as alerts_db
import app.db.metrics_db as metrics_db
import app.db.sensor_db as sensor_db
import app.db.ventilation_db as ventilation_db


def test_insert_sensor_reading_persists_payload(tmp_path, monkeypatch):
    db_path = tmp_path / "sensor.db"
    monkeypatch.setattr(sensor_db, "SENSOR_DB_PATH", str(db_path))

    sensor_db.init_sensor_db()

    reading = {
        "timestamp": "2025-02-01T12:00:00Z",
        "temp": 45.5,
        "pressure": 950.1,
        "co_mean": 115.2,
        "co_max": 260.4,
        "co_valid": True,
        "pm2_5": 88.0,
        "pm10": 120.0,
    }

    sensor_db.insert_sensor_reading(reading)

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT timestamp, temp, pressure, co_mean, co_max, co_valid, pm2_5, pm10
            FROM sensor_readings
            """
        ).fetchone()

    assert row == (
        reading["timestamp"],
        reading["temp"],
        reading["pressure"],
        reading["co_mean"],
        reading["co_max"],
        1,  # True becomes 1 in the DB
        reading["pm2_5"],
        reading["pm10"],
    )


def test_insert_sensor_reading_stores_false_flag_and_extremes(tmp_path, monkeypatch):
    """Verify boolean false is stored as 0 and extreme floats persist untouched."""

    db_path = tmp_path / "sensor.db"
    monkeypatch.setattr(sensor_db, "SENSOR_DB_PATH", str(db_path))

    sensor_db.init_sensor_db()

    reading = {
        "timestamp": "2025-02-01T12:00:01Z",
        "temp": -12.75,
        "pressure": 1105.4,
        "co_mean": 0.0,
        "co_max": 0.5,
        "co_valid": False,
        "pm2_5": 0.01,
        "pm10": 5.5,
    }

    sensor_db.insert_sensor_reading(reading)

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT timestamp, temp, pressure, co_mean, co_max, co_valid, pm2_5, pm10
            FROM sensor_readings
            """
        ).fetchone()

    assert row == (
        reading["timestamp"],
        reading["temp"],
        reading["pressure"],
        reading["co_mean"],
        reading["co_max"],
        0,  # False becomes 0 in the DB
        reading["pm2_5"],
        reading["pm10"],
    )


def test_insert_metric_record_stores_critical_value(tmp_path, monkeypatch):
    db_path = tmp_path / "metrics.db"
    monkeypatch.setattr(metrics_db, "METRICS_DB_PATH", str(db_path))

    metrics_db.init_metrics_db()

    metric = {
        "timestamp": "2025-02-01T12:05:00Z",
        "type": "CO_CEILING",
        "value": 260.4,
        "window": "15m",
        "limit": 100.0,
        "status": "critical",
    }

    metrics_db.insert_metric_record(metric)

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT timestamp, metric_type, value, window, limit_value, status
            FROM metrics
            """
        ).fetchone()

    assert row == (
        metric["timestamp"],
        metric["type"],
        metric["value"],
        metric["window"],
        metric["limit"],
        metric["status"],
    )


@pytest.mark.parametrize(
    "status, limit_value",
    [
        ("yellow", 22.0),
        ("orange", 30.0),
        ("red", 33.0),
    ],
)
def test_insert_metric_record_preserves_status_colors(tmp_path, monkeypatch, status, limit_value):
    """Multiple inserts keep the requested color/status text intact."""

    db_path = tmp_path / "metrics.db"
    monkeypatch.setattr(metrics_db, "METRICS_DB_PATH", str(db_path))

    metrics_db.init_metrics_db()

    metric = {
        "timestamp": "2025-02-01T12:05:01Z",
        "type": "TEMP_LEVEL",
        "value": 29.1,
        "window": "instant",
        "limit": limit_value,
        "status": status,
    }

    metrics_db.insert_metric_record(metric)

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT status, limit_value
            FROM metrics
            WHERE metric_type = ?
            """,
            (metric["type"],),
        ).fetchone()

    assert row == (status, limit_value)


def test_insert_alert_record_writes_severity(tmp_path, monkeypatch):
    db_path = tmp_path / "alerts.db"
    monkeypatch.setattr(alerts_db, "ALERTS_DB_PATH", str(db_path))

    alerts_db.init_alerts_db()

    alert = {
        "timestamp": "2025-02-01T12:10:00Z",
        "category": "PM10",
        "value": 200.0,
        "limit": 150.0,
        "severity": "critical",
        "message": "PM10 critical; evacuate area",
    }

    alerts_db.insert_alert_record(alert)

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT timestamp, category, value, limit_value, severity, message
            FROM alerts
            """
        ).fetchone()

    assert row == (
        alert["timestamp"],
        alert["category"],
        alert["value"],
        alert["limit"],
        alert["severity"],
        alert["message"],
    )


def test_insert_alert_record_handles_warning_and_message(tmp_path, monkeypatch):
    db_path = tmp_path / "alerts.db"
    monkeypatch.setattr(alerts_db, "ALERTS_DB_PATH", str(db_path))

    alerts_db.init_alerts_db()

    alert = {
        "timestamp": "2025-02-01T12:10:01Z",
        "category": "PRESSURE",
        "value": 900.0,
        "limit": 950.0,
        "severity": "warning",
        "message": "Pressure warning band triggered",
    }

    alerts_db.insert_alert_record(alert)

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT severity, message
            FROM alerts
            WHERE category = ?
            """,
            (alert["category"],),
        ).fetchone()

    assert row == ("warning", "Pressure warning band triggered")


def test_insert_ventilation_record_serializes_reasons(tmp_path, monkeypatch):
    db_path = tmp_path / "ventilation.db"
    monkeypatch.setattr(ventilation_db, "VENTILATION_DB_PATH", str(db_path))

    ventilation_db.init_ventilation_db()

    record = {
        "timestamp": "2025-02-01T12:15:00Z",
        "ventilation_mode": "EMERGENCY_PURGE",
        "fan_supply_speed": 40,
        "fan_exhaust_speed": 100,
        "ac_power": 0,
        "reasons": ["CO ceiling critical", "Emergency purge engaged"],
    }

    ventilation_db.insert_ventilation_record(record)

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT timestamp, mode, fan_supply, fan_exhaust, ac_power, reasons
            FROM ventilation_history
            """
        ).fetchone()

    assert row[:5] == (
        record["timestamp"],
        record["ventilation_mode"],
        record["fan_supply_speed"],
        record["fan_exhaust_speed"],
        record["ac_power"],
    )
    assert json.loads(row[5]) == record["reasons"]


def test_insert_ventilation_record_handles_empty_reasons(tmp_path, monkeypatch):
    db_path = tmp_path / "ventilation.db"
    monkeypatch.setattr(ventilation_db, "VENTILATION_DB_PATH", str(db_path))

    ventilation_db.init_ventilation_db()

    record = {
        "timestamp": "2025-02-01T12:16:00Z",
        "ventilation_mode": "NORMAL",
        "fan_supply_speed": 40,
        "fan_exhaust_speed": 30,
        "ac_power": 0,
        "reasons": [],
    }

    ventilation_db.insert_ventilation_record(record)

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT reasons
            FROM ventilation_history
            WHERE mode = ?
            """,
            (record["ventilation_mode"],),
        ).fetchone()

    assert json.loads(row[0]) == []