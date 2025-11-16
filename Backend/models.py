def validate_payload(data):
    required = [
        "timestamp", "temp", "pressure",
        "co_mean", "co_max", "co_valid",
        "pm2_5", "pm10"
    ]

    for r in required:
        if r not in data:
            raise ValueError(f"Missing field: {r}")

    return {
        "timestamp": data["timestamp"],
        "temp": float(data["temp"]),
        "pressure": float(data["pressure"]),
        "co_mean": float(data["co_mean"]),
        "co_max": float(data["co_max"]),
        "co_valid": bool(data["co_valid"]),
        "pm2_5": float(data["pm2_5"]),
        "pm10": float(data["pm10"])
    }
