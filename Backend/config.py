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
