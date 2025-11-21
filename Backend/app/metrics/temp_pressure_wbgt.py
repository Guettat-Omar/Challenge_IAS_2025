from app.config.thresholds import TEMP_LIMITS, PRESSURE_LIMITS, WBGT_LIMITS


def compute_wbgt(temp, humidity=40):
    # simplified WBGT approximation
    return 0.567 * temp + 0.393 * humidity + 3.94


def _classify(value, limits):
    for level, (low, high) in limits.items():
        if low <= value < high:
            return level, low, high
    return "unknown", None, None


def classify_temp(temp):
    return _classify(temp, TEMP_LIMITS)


def classify_pressure(p):
    return _classify(p, PRESSURE_LIMITS)


def classify_wbgt(w):
    return _classify(w, WBGT_LIMITS)
