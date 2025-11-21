# CO
CO_CEILING = 300
CO_STEL = 200
CO_TWA = 50

# PM2.5
PM25_LIMITS = {
    "green": (0, 15),
    "yellow": (15, 35),
    "orange": (35, 75),
    "red": (75, 250),
    "dark-red": (250, 3000),
    "purple": (3000, 999999),
}

# PM10
PM10_LIMITS = {
    "green": (0, 40),
    "yellow": (40, 80),
    "orange": (80, 150),
    "red": (150, 300),
    "dark-red": (300, 10000),
    "purple": (10000, 999999),
}

# Temperature
TEMP_LIMITS = {
    "cold": (-50, 5),
    "normal": (5, 30),
    "hot": (30, 38),
    "veryhot": (38, 50),
}

# Pressure
PRESSURE_LIMITS = {
    "low": (0, 980),
    "normal": (980, 1030),
    "high": (1030, 2000),
}

# WBGT
WBGT_LIMITS = {
    "safe": (0, 25),
    "caution": (25, 28),
    "extreme": (28, 35),
    "danger": (35, 100),
}
