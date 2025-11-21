# Databases
SENSOR_DB_PATH = "sensor_data.db"
METRICS_DB_NAME = "metrics.db"

# STEL/TWA windows in minutes
STEL_WINDOW_MINUTES = 15
TWA_WINDOW_MINUTES = 8 * 60  # 480 minutes

# OSHA/NIOSH CO Exposure Limits
CO_CEILING_LIMIT = 300.0     # ppm, immediate danger peak
CO_STEL_LIMIT    = 200.0     # ppm, 15 min average
CO_TWA_LIMIT     = 50.0      # ppm, 8h average

# MQTT
MQTT_SERVER = "broker.hivemq.com"
MQTT_PORT   = 1883
MQTT_TOPIC  = "omar/factory/sensors"

# ---- PM2.5 RANGES (DSM501A realistic) ----
# Values in µg/m³
PM25_THRESHOLDS = [
    ("green",    0.0,   15.0),
    ("yellow",   15.0,  30.0),
    ("orange",   30.0,  60.0),
    ("red",      60.0, 100.0),
    ("dark_red", 100.0, float("inf")),
]
# ---- PM10 RANGES (DSM501A realistic) ----
PM10_THRESHOLDS = [
    ("green",    0.0,   40.0),
    ("yellow",   40.0,  80.0),
    ("orange",   80.0, 120.0),
    ("red",      120.0,150.0),
    ("dark_red", 150.0,float("inf")),
]