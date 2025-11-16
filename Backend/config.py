# config.py

# Main measurements DB
DB_NAME = "measurements.db"

# Separate DB for exposure metrics (STEL, TWA, CEILING)
METRICS_DB_NAME = "metrics.db"

# Windows (in minutes)
STEL_WINDOW_MINUTES = 15             # 15-minute STEL window
TWA_WINDOW_MINUTES = 8 * 60          # 8 hours = 480 minutes

# CO limits ("caps") – in the same unit as co_mean / co_max
# ⚠️ You MUST tune these based on calibration later
CO_CEILING_LIMIT = 300.0             # instant dangerous peak
CO_STEL_LIMIT    = 200.0             # short-term limit
CO_TWA_LIMIT     = 50.0              # long-term limit
