import json
import paho.mqtt.client as mqtt

from config import MQTT_SERVER, MQTT_PORT, MQTT_TOPIC
from models import validate_payload
from db import insert_reading
from co_metrics import update_co_metrics


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        data = validate_payload(payload)

        print("\n📥 Received:")
        print(data)

        insert_reading(data)
        update_co_metrics(data["timestamp"])

    except Exception as e:
        print("❌ Error:", e)


def start_listener():
    print("🚀 MQTT Listener ready...")
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(MQTT_SERVER, MQTT_PORT, keepalive=60)
    client.subscribe(MQTT_TOPIC)
    client.loop_forever()
