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
        payload_str = msg.payload.decode()
        data_raw = json.loads(payload_str)
        data = validate_payload(data_raw)

        # 1) Store minute reading in main DB
        insert_reading(data)

        print("\n📥 Received data from ESP32:")
        print(data)

        # 2) Compute exposure metrics (STEL, TWA, CEILING)
        exposure = evaluate_exposure(data["co_max"])

        # 3) Log each metric in metrics DB
        for metric_type, info in exposure.items():
            insert_metric(
                metric_type=metric_type,
                value=info["value"],
                limit=info["limit"],
                exceeded=info["exceeded"],
            )

        # 4) Print for debug / warning monitoring
        stel = exposure["STEL"]
        twa  = exposure["TWA"]
        ceil = exposure["CEILING"]

        print("📊 Exposure metrics:")
        print(f"  STEL:    value={stel['value']}  limit={stel['limit']}  exceeded={stel['exceeded']}")
        print(f"  TWA:     value={twa['value']}   limit={twa['limit']}   exceeded={twa['exceeded']}")
        print(f"  CEILING: value={ceil['value']} limit={ceil['limit']} exceeded={ceil['exceeded']}")

    except Exception as e:
        print("❌ Error in on_message:", e)


def start_listener():
    print("🚀 MQTT listener started...")
    client = mqtt.Client()
    client.on_message = on_message

    client.connect(MQTT_SERVER, MQTT_PORT, keepalive=60)
    client.subscribe(MQTT_TOPIC)

    client.loop_forever()
