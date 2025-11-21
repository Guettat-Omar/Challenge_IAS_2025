from app.metrics.co_metrics import compute_co_ceiling
from app.metrics.pm_metrics import process_pm_metrics
from app.metrics.temp_pressure_wbgt import compute_wbgt, classify_temp, classify_pressure, classify_wbgt
from app.metrics.co_alerts import process_co_alerts


def evaluate_all_metrics(reading):
    ts = reading["timestamp"]

    metrics = []
    alerts = []

    # -------------------------
    # CO Ceiling (instant)
    # -------------------------
    co_ceiling_m = compute_co_ceiling(ts, reading["co_max"])
    metrics.append(co_ceiling_m)

    # -------------------------
    # PM Metrics
    # -------------------------
    pm = process_pm_metrics(ts, reading["pm2_5"], reading["pm10"])
    # Alerts are generated inside process_pm_metrics

    # -------------------------
    # CO STEL/TWA Alerts
    # (you can integrate STEL/TWA code)
    # -------------------------
    co_stel = None       # compute if needed
    co_twa = None        # compute if needed
    ceiling = reading["co_max"]

    co_alert_list = process_co_alerts(ts, co_stel, co_twa, ceiling)
    alerts.extend(co_alert_list)

    # -------------------------
    # Temperature / Pressure
    # -------------------------
    temp_lvl = classify_temp(reading["temp"])
    pressure_lvl = classify_pressure(reading["pressure"])

    # WBGT  (approx)
    wbgt_val = compute_wbgt(reading["temp"])
    wbgt_lvl = classify_wbgt(wbgt_val)

    # Add them as passive metrics (no alerts yet)
    metrics.append({
        "timestamp": ts,
        "type": "TEMP_LEVEL",
        "value": reading["temp"],
        "window": "instant",
        "limit": temp_lvl[2],
        "status": temp_lvl[0]
    })

    metrics.append({
        "timestamp": ts,
        "type": "PRESSURE_LEVEL",
        "value": reading["pressure"],
        "window": "instant",
        "limit": pressure_lvl[2],
        "status": pressure_lvl[0]
    })

    metrics.append({
        "timestamp": ts,
        "type": "WBGT",
        "value": wbgt_val,
        "window": "instant",
        "limit": wbgt_lvl[2],
        "status": wbgt_lvl[0]
    })

    return {
        "metrics": metrics,
        "alerts": alerts
    }
