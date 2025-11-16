# db.py

import sqlite3
from config import DB_NAME


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS readings (
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
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO readings (timestamp, temp, pressure, co_mean, co_max, co_valid, pm2_5, pm10)
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


def get_last_n_minutes(n: int):
    """Fetch the last n co_mean values for STEL/TWA."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        SELECT co_mean FROM readings
        ORDER BY id DESC
        LIMIT ?
    """, (n,))

    values = [row[0] for row in cur.fetchall()]
    conn.close()
    return values
