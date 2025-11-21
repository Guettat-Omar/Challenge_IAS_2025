import sqlite3
from config import METRICS_DB_NAME

def get_metrics_conn():
    return sqlite3.connect(METRICS_DB_NAME)

def init_metrics_db():
    conn = get_metrics_conn()
    cur = conn.cursor()

    # ---- CO METRICS TABLE (TWA, STEL, CEILING) ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS co_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            metric_type TEXT NOT NULL,      -- TWA, STEL, CEILING
            value REAL NOT NULL,
            window TEXT NOT NULL,           -- 8h, 15min, instant
            limit_value REAL NOT NULL,
            is_safe INTEGER NOT NULL        -- 1 = safe, 0 = alert
        )
    """)
    # ---- ALERTS TABLE (generic for PM, CO, Temp, etc.) ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            param TEXT NOT NULL,            -- PM2.5, PM10, CO, TEMP...
            value REAL NOT NULL,
            level TEXT NOT NULL,            -- green, yellow, orange, red, dark_red
            severity TEXT NOT NULL,         -- none, warning, high, critical
            threshold_low REAL,
            threshold_high REAL,
            message TEXT
        )
    """)

    conn.commit()
    conn.close()

def insert_alert(timestamp: str,
                 param: str,
                 value: float,
                 level: str,
                 severity: str,
                 threshold_low: float | None,
                 threshold_high: float | None,
                 message: str):
    """
    Insert a generic alert in the alerts table.
    """
    conn = get_metrics_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO alerts
        (timestamp, param, value, level, severity, threshold_low, threshold_high, message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (timestamp, param, value, level, severity, threshold_low, threshold_high, message),
    )

    conn.commit()
    conn.close()
