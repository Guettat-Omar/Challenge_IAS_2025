# mqtt_listener.py

import json
import paho.mqtt.client as mqtt

from models import validate_payload
from db import insert_reading
from stel_twa import evaluate_exposure
from metrics_db import insert_metric

MQTT_TOPIC = "omar/factory/sensors"
MQTT_SERVER = "broker.hivemq.com"
MQTT_PORT = 1883


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        data = validate_payload(payload)

        insert_reading(data)

        print("\n📥 Received:")
        print(data)

        # Compute exposure metrics
        exposure = evaluate_exposure(data["co_max"])

        # Store each metric in metric DB
        for metric_name, m in exposure.items():
            insert_metric(
                metric_type=metric_name,
                value=m["value"],
                limit=m["limit"],
                exceeded=m["exceeded"]
            )

        # Debug output
        print("📊 Exposure metrics:")
        for k, v in exposure.items():
            print(f"  {k}: value={v['value']} limit={v['limit']} exceeded={v['exceeded']}")

    except Exception as e:
        print("❌ Error:", e)


def start_listener():
    print("🚀 MQTT Listener ready...")
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(MQTT_SERVER, MQTT_PORT, keepalive=60)
    client.subscribe(MQTT_TOPIC)
    client.loop_forever()
