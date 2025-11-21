from db import init_db
from metrics_db import init_metrics_db
from mqtt_listener import start_listener

if __name__ == "__main__":
    init_db()
    init_metrics_db()
    start_listener()
