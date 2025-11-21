import sqlite3
from datetime import datetime, timedelta

from metrics_db import get_metrics_conn
from config import (
    SENSOR_DB_PATH, CO_TWA_LIMIT,
    CO_STEL_LIMIT, CO_CEILING_LIMIT
)


def get_sensor_conn():
    return sqlite3.connect(SENSOR_DB_PATH)


def _parse_ts(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")


def _insert_metric(timestamp, metric_type, value, window, limit_value, is_safe):
    conn = get_metrics_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO co_metrics (timestamp, metric_type, value, window, limit_value, is_safe)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (timestamp, metric_type, value, window, limit_value, 1 if is_safe else 0))

    conn.commit()
    conn.close()


def _compute_window_avg(conn_sensor, end_ts, minutes):
    dt_end = _parse_ts(end_ts)
    dt_start = dt_end - timedelta(minutes=minutes)

    cur = conn_sensor.cursor()
    cur.execute("""
        SELECT co_mean
        FROM sensor_readings
        WHERE timestamp BETWEEN ? AND ?
          AND co_valid = 1
    """, (
        dt_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        end_ts
    ))

    rows = cur.fetchall()
    if not rows:
        return None

    values = [r[0] for r in rows if r[0] is not None]
    return sum(values) / len(values) if values else None


def _get_latest_comax(conn_sensor, end_ts):
    cur = conn_sensor.cursor()
    cur.execute("""
        SELECT co_max
        FROM sensor_readings
        WHERE timestamp <= ?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (end_ts,))
    row = cur.fetchone()
    return row[0] if row else None

def update_co_metrics(last_timestamp: str):
    """
    Computes and stores CO metrics (TWA, STEL, CEILING).
    Returns the three values so co_alerts.py can evaluate alerts.
    """
    conn_sensor = get_sensor_conn()

    # --- Compute metrics ---
    twa_value = _compute_window_avg(conn_sensor, last_timestamp, minutes=480)
    stel_value = _compute_window_avg(conn_sensor, last_timestamp, minutes=15)
    ceiling_value = _get_latest_comax(conn_sensor, last_timestamp)

    # --- Store metrics in co_metrics table ---
    if twa_value is not None:
        _insert_metric(last_timestamp, "TWA", twa_value, "8h", CO_TWA_LIMIT, twa_value <= CO_TWA_LIMIT)

    if stel_value is not None:
        _insert_metric(last_timestamp, "STEL", stel_value, "15min", CO_STEL_LIMIT, stel_value <= CO_STEL_LIMIT)

    if ceiling_value is not None:
        _insert_metric(last_timestamp, "CEILING", ceiling_value, "instant", CO_CEILING_LIMIT, ceiling_value <= CO_CEILING_LIMIT)

    conn_sensor.close()

    # Return metrics to alert module
    return {
        "twa": twa_value,
        "stel": stel_value,
        "ceiling": ceiling_value
    }

