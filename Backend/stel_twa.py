# stel_twa.py

from config import (
    STEL_WINDOW_MINUTES,
    TWA_WINDOW_MINUTES,
    CO_CEILING_LIMIT,
    CO_STEL_LIMIT,
    CO_TWA_LIMIT,
)
from db import get_last_n_minutes


def compute_stel():
    """Progressive STEL (15-minute): uses available samples."""
    vals = get_last_n_minutes(STEL_WINDOW_MINUTES)
    if not vals:
        return None
    return round(sum(vals) / len(vals), 2)


def compute_twa():
    """Progressive TWA (8-hour): uses available samples."""
    vals = get_last_n_minutes(TWA_WINDOW_MINUTES)
    if not vals:
        return None
    return round(sum(vals) / len(vals), 2)


def check_ceiling(latest_co_max):
    """Ceiling uses last minute’s CO max."""
    return latest_co_max


def evaluate_exposure(latest_co_max: float):
    stel_val = compute_stel()
    twa_val  = compute_twa()
    ceil_val = check_ceiling(latest_co_max)

    return {
        "STEL": {
            "value": stel_val,
            "limit": CO_STEL_LIMIT,
            "exceeded": stel_val is not None and stel_val > CO_STEL_LIMIT
        },
        "TWA": {
            "value": twa_val,
            "limit": CO_TWA_LIMIT,
            "exceeded": twa_val is not None and twa_val > CO_TWA_LIMIT
        },
        "CEILING": {
            "value": ceil_val,
            "limit": CO_CEILING_LIMIT,
            "exceeded": ceil_val is not None and ceil_val > CO_CEILING_LIMIT
        }
    }
