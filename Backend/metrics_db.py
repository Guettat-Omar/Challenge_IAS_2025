# metrics_db.py

import sqlite3
from datetime import datetime, timezone
from config import METRICS_DB_NAME


def init_metrics_db():
    conn = sqlite3.connect(METRICS_DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            metric_type TEXT,
            value REAL,
            limit_value REAL,
            exceeded INTEGER
        )
    """)

    conn.commit()
    conn.close()


def insert_metric(metric_type: str, value: float, limit: float, exceeded: bool):
    if value is None:
        return  # nothing to store yet

    conn = sqlite3.connect(METRICS_DB_NAME)
    cur = conn.cursor()

    now = datetime.now(timezone.utc).isoformat()

    cur.execute("""
        INSERT INTO metrics (timestamp, metric_type, value, limit_value, exceeded)
        VALUES (?, ?, ?, ?, ?)
    """, (now, metric_type, value, limit, 1 if exceeded else 0))

    conn.commit()
    conn.close()
