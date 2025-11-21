import sqlite3
from config import METRICS_DB_NAME

def get_metrics_conn():
    return sqlite3.connect(METRICS_DB_NAME)

def init_metrics_db():
    conn = get_metrics_conn()
    cur = conn.cursor()

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

    conn.commit()
    conn.close()
