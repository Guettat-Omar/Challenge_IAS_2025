# mqtt_listener.py

import json
import paho.mqtt.client as mqtt

from config import MQTT_SERVER, MQTT_PORT, MQTT_TOPIC
from models import validate_payload
from db import insert_reading

from co_metrics import update_co_metrics
from co_alerts import process_co_alerts       # <-- NEW
from pm_metrics import process_pm_metrics     # <-- already added


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        data = validate_payload(payload)

        print("\n📥 Received:", data)

        # 1. Store raw reading
        insert_reading(data)

        # 2. CO metrics (TWA/STEL/Ceiling)
        co_metrics = update_co_metrics(data["timestamp"])

        # 3. Create CO alerts
        process_co_alerts(
            timestamp=data["timestamp"],
            stel=co_metrics["stel"],
            twa=co_metrics["twa"],
            ceiling=co_metrics["ceiling"]
        )

        # 4. PM2.5 & PM10 alerts
        process_pm_metrics(
            timestamp=data["timestamp"],
            pm25=data["pm2_5"],
            pm10=data["pm10"]
        )

    except Exception as e:
        print("❌ Error:", e)


def start_listener():
    print("🚀 MQTT Listener ready...")
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(MQTT_SERVER, MQTT_PORT, keepalive=60)
    client.subscribe(MQTT_TOPIC)
    client.loop_forever()
