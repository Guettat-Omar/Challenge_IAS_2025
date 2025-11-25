import json
import paho.mqtt.client as mqtt

from app.models.validate_payload import validate_payload
from app.db.sensor_db import insert_sensor_reading
from app.metrics.evaluator import evaluate_all_metrics
from app.db.metrics_db import insert_metric_record
from app.db.alerts_db import insert_alert_record
from app.db.ventilation_db import insert_ventilation_record
from app.hvac.hvac_controller import decide_hvac_actions
from app.config.config import MQTT_SERVER, MQTT_PORT, MQTT_TOPIC, MQTT_VENTILATION_TOPIC


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        reading = validate_payload(data)

        insert_sensor_reading(reading)

        results = evaluate_all_metrics(reading)

        # Store metrics
        for m in results["metrics"]:
            insert_metric_record(m)

        # Store alerts
        for a in results["alerts"]:
            insert_alert_record(a)

        status_packet = results["results"]["status_packet"]
        ventilation_actions = decide_hvac_actions(status_packet)
        insert_ventilation_record(ventilation_actions)

        publish_payload = dict(ventilation_actions)
        publish_payload.pop("reasons", None)

        client.publish(MQTT_VENTILATION_TOPIC, json.dumps(publish_payload))

        print("\n📥 Received:", reading)
        print("📊 Stored metrics, alerts, and ventilation actions.")
        print(f"📡 Published ventilation commands : {publish_payload}")

    except Exception as e:
        print("❌ Error:", e)


def start_listener():
    print("🚀 MQTT Listener ready...")
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(MQTT_SERVER, MQTT_PORT)
    client.subscribe(MQTT_TOPIC)
    client.loop_forever()
