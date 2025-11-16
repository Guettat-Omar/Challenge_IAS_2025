# config.py

# Databases
DB_NAME = "measurements.db"
METRICS_DB_NAME = "metrics.db"

# STEL/TWA windows
STEL_WINDOW_MINUTES = 15
TWA_WINDOW_MINUTES = 8 * 60  # 480 minutes

# CO Exposure Limits (temporary values, adjust after calibration)
CO_CEILING_LIMIT = 300.0   # immediate danger peak
CO_STEL_LIMIT    = 200.0   # short-term exposure limit
CO_TWA_LIMIT     = 50.0    # long-term exposure limit
