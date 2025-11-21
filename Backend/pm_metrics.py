from metrics_db import insert_alert
from config import PM25_THRESHOLDS, PM10_THRESHOLDS

def _map_level_to_severity(level: str) -> str:
    """
    Map color level to alert severity.
    You can tune this:
      - green  -> none
      - yellow -> none (just info)
      - orange -> warning
      - red    -> high
      - dark_red -> critical
    """
    if level == "green":
        return "none"
    if level == "yellow":
        return "none"   # or "info" if you add such severity
    if level == "orange":
        return "warning"
    if level == "red":
        return "high"
    if level == "dark_red":
        return "critical"
    return "none"



def _classify(value: float, thresholds: list[tuple[str, float, float]]):
    """
    Generic classifier: returns (level, low, high) for the given value
    based on thresholds list of (level, low, high).
    """
    for level, low, high in thresholds:
        if low <= value < high:
            return level, low, high
    # fallback (should not happen if last threshold is +inf)
    return "unknown", None, None

def classify_pm25(value: float):
    """
    Return (level, severity, low, high) for PM2.5 value.
    """
    level, low, high = _classify(value, PM25_THRESHOLDS)
    severity = _map_level_to_severity(level)
    return level, severity, low, high

def classify_pm10(value: float):
    """
    Return (level, severity, low, high) for PM10 value.
    """
    level, low, high = _classify(value, PM10_THRESHOLDS)
    severity = _map_level_to_severity(level)
    return level, severity, low, high

def process_pm_metrics(timestamp: str, pm25: float, pm10: float):
    """
    Called every minute after receiving sensor data.

    - Classifies PM2.5 and PM10 into color levels.
    - If severity is not 'none', inserts an alert.
    - You can later extend this to also save PM metrics in a metrics table.
    """
    # ---- PM2.5 ----
    level25, sev25, low25, high25 = classify_pm25(pm25)
    if sev25 != "none":
        msg25 = f"PM2.5={pm25:.2f} µg/m³ is {level25.upper()} (range {low25}-{high25} µg/m³)"
        insert_alert(
            timestamp=timestamp,
            param="PM2.5",
            value=pm25,
            level=level25,
            severity=sev25,
            threshold_low=low25,
            threshold_high=high25,
            message=msg25,
        )

    # ---- PM10 ----
    level10, sev10, low10, high10 = classify_pm10(pm10)
    if sev10 != "none":
        msg10 = f"PM10={pm10:.2f} µg/m³ is {level10.upper()} (range {low10}-{high10} µg/m³)"
        insert_alert(
            timestamp=timestamp,
            param="PM10",
            value=pm10,
            level=level10,
            severity=sev10,
            threshold_low=low10,
            threshold_high=high10,
            message=msg10,
        )

    # (Optional) return classification info if you need it in the future
    return {
        "pm2_5": {
            "value": pm25,
            "level": level25,
            "severity": sev25,
            "range": (low25, high25),
        },
        "pm10": {
            "value": pm10,
            "level": level10,
            "severity": sev10,
            "range": (low10, high10),
        },
    }