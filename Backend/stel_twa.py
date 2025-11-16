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
    """
    Compute 15-minute STEL.
    If less than 15 readings → progressive STEL = average of what we have.
    """
    values = get_last_n_minutes(STEL_WINDOW_MINUTES)
    if not values:
        return None

    stel = sum(values) / len(values)
    return round(stel, 2)


def compute_twa():
    """
    Compute 8-hour TWA.
    If less than 480 readings → progressive TWA = average of what we have.
    """
    values = get_last_n_minutes(TWA_WINDOW_MINUTES)
    if not values:
        return None

    twa = sum(values) / len(values)
    return round(twa, 2)


def check_ceiling(latest_co_max: float | None):
    """
    Ceiling check based on the latest CO max value from ESP32.
    """
    if latest_co_max is None:
        return None
    return latest_co_max


def evaluate_exposure(latest_co_max: float | None):
    """
    Compute STEL, TWA, and ceiling and compare each one to its cap.

    Returns a dict like:
    {
      "STEL":    {"value": ..., "limit": ..., "exceeded": bool},
      "TWA":     {"value": ..., "limit": ..., "exceeded": bool},
      "CEILING": {"value": ..., "limit": ..., "exceeded": bool},
    }
    """

    stel_value = compute_stel()
    twa_value  = compute_twa()
    ceil_value = check_ceiling(latest_co_max)

    stel_exceeded = stel_value is not None and stel_value > CO_STEL_LIMIT
    twa_exceeded  = twa_value is not None and twa_value > CO_TWA_LIMIT
    ceil_exceeded = ceil_value is not None and ceil_value > CO_CEILING_LIMIT

    return {
        "STEL": {
            "value": stel_value,
            "limit": CO_STEL_LIMIT,
            "exceeded": stel_exceeded,
        },
        "TWA": {
            "value": twa_value,
            "limit": CO_TWA_LIMIT,
            "exceeded": twa_exceeded,
        },
        "CEILING": {
            "value": ceil_value,
            "limit": CO_CEILING_LIMIT,
            "exceeded": ceil_exceeded,
        },
    }
