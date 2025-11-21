# co_alerts.py

from metrics_db import insert_alert
from config import (
    CO_TWA_LIMIT,
    CO_STEL_LIMIT,
    CO_CEILING_LIMIT
)

def process_co_alerts(timestamp: str, stel: float | None, twa: float | None, ceiling: float):
    """
    Generate alerts for CO if limits are exceeded.
    Alerts stored in the same `alerts` table used for PM.
    """

    # --- CEILING (instant dangerous peak) ---
    if ceiling is not None and ceiling > CO_CEILING_LIMIT:
        msg = f"CO CEILING ALERT: Peak={ceiling:.2f} ppm > limit {CO_CEILING_LIMIT} ppm"
        insert_alert(
            timestamp=timestamp,
            param="CO_CEILING",
            value=ceiling,
            level="red",          # Always red → dangerous
            severity="critical",
            threshold_low=None,
            threshold_high=CO_CEILING_LIMIT,
            message=msg,
        )

    # --- STEL (last 15 min) ---
    if stel is not None and stel > CO_STEL_LIMIT:
        msg = f"CO STEL EXCEEDED: {stel:.2f} ppm > limit {CO_STEL_LIMIT} ppm"
        insert_alert(
            timestamp=timestamp,
            param="CO_STEL",
            value=stel,
            level="orange",
            severity="high",
            threshold_low=None,
            threshold_high=CO_STEL_LIMIT,
            message=msg,
        )

    # --- TWA (8 hours) ---
    if twa is not None and twa > CO_TWA_LIMIT:
        msg = f"CO TWA EXCEEDED: {twa:.2f} ppm > limit {CO_TWA_LIMIT} ppm"
        insert_alert(
            timestamp=timestamp,
            param="CO_TWA",
            value=twa,
            level="orange",
            severity="warning",
            threshold_low=None,
            threshold_high=CO_TWA_LIMIT,
            message=msg,
        )
