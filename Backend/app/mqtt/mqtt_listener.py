import json
import paho.mqtt.client as mqtt

from app.models.validate_payload import validate_payload
from app.db.sensor_db import insert_sensor_reading
from app.metrics.evaluator import evaluate_all_metrics
from app.db.metrics_db import insert_metric_record
from app.db.alerts_db import insert_alert_record
from app.db.ventilation_db import insert_ventilation_record
from app.hvac.hvac_controller import decide_hvac_actions
from app.config.config import (
    MQTT_SERVER,
    MQTT_PORT,
    MQTT_TOPIC,
    MQTT_UNITY_TOPIC,
    MQTT_VENTILATION_TOPIC,
)


def _extract_color(level: str) -> str:
    sanitized = (level or "").replace("_", "-")
    return sanitized.split("-")[0] if "-" in sanitized else sanitized or "unknown"


def build_unity_payload(status_packet):
    return {
        "timestamp": status_packet.get("timestamp"),
        "co": _extract_color(status_packet.get("co", {}).get("level", "")),
        "pm2_5": _extract_color(
            status_packet.get("pm", {}).get("pm2_5", {}).get("level", "")
        ),
        "pm10": _extract_color(
            status_packet.get("pm", {}).get("pm10", {}).get("level", "")
        ),
        "temp": _extract_color(status_packet.get("temp", {}).get("level", "")),
        "wbgt": _extract_color(status_packet.get("wbgt", {}).get("level", "")),
        "pressure": _extract_color(status_packet.get("pressure", {}).get("level", "")),
    }


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
        unity_payload = build_unity_payload(status_packet)
        client.publish(MQTT_UNITY_TOPIC, json.dumps(unity_payload))

        print("\n📥 Received:", reading)
        print("📊 Stored metrics, alerts, and ventilation actions.")
        print(f"📡 Published ventilation commands : {publish_payload}")
        print(f"🎮 Sent Unity status payload: {unity_payload}")

    except Exception as e:
        print("❌ Error:", e)


def start_listener():
    print("🚀 MQTT Listener ready...")
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(MQTT_SERVER, MQTT_PORT)
    client.subscribe(MQTT_TOPIC)
    client.loop_forever()