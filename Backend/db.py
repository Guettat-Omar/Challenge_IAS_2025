import sqlite3
from config import SENSOR_DB_PATH


def init_db():
    conn = sqlite3.connect(SENSOR_DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            temp REAL,
            pressure REAL,
            co_mean REAL,
            co_max REAL,
            co_valid INTEGER,
            pm2_5 REAL,
            pm10 REAL
        )
    """)

    conn.commit()
    conn.close()


def insert_reading(data: dict):
    """Insert raw sensor values into sensor_readings table."""
    conn = sqlite3.connect(SENSOR_DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO sensor_readings
        (timestamp, temp, pressure, co_mean, co_max, co_valid, pm2_5, pm10)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["timestamp"],
        data["temp"],
        data["pressure"],
        data["co_mean"],
        data["co_max"],
        1 if data["co_valid"] else 0,
        data["pm2_5"],
        data["pm10"]
    ))

    conn.commit()
    conn.close()
