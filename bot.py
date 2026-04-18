import requests
import json
import pandas as pd
from datetime import datetime
import time

print("🧠 ALADDIN DATA ENGINE")

# ==============================
# CARGAR TAREA
# ==============================
with open("task.json") as f:
    task = json.load(f)

# ==============================
# CONVERTIR FECHA A TIMESTAMP
# ==============================
def to_milliseconds(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return int(dt.timestamp() * 1000)

# ==============================
# DESCARGAR DATOS BINANCE
# ==============================
def get_klines(symbol, interval, start, end):
    url = "https://api.binance.com/api/v3/klines"

    start_ts = to_milliseconds(start)
    end_ts = to_milliseconds(end)

    all_data = []

    while start_ts < end_ts:
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": start_ts,
            "limit": 1000
        }

        response = requests.get(url, params=params)
        data = response.json()

        if not data:
            break

        all_data.extend(data)
        start_ts = data[-1][0] + 1

        time.sleep(0.2)  # evitar rate limit

    return all_data

# ==============================
# FORMATEAR DATAFRAME
# ==============================
def to_dataframe(data):
    df = pd.DataFrame(data, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "qav", "trades", "tbbav", "tbqav", "ignore"
    ])

    df["timestamp"] = pd.to_datetime(df["timestamp"], unit='ms')

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)

    return df

# ==============================
# GUARDAR CSV
# ==============================
def save_csv(df, symbol, interval):
    filename = f"{symbol}_{interval}.csv"
    df.to_csv(filename, index=False)
    print(f"📁 Guardado: {filename}")

# ==============================
# EJECUCIÓN
# ==============================
if task["task"] == "download_data":
    symbol = task["symbol"]
    start = task["start"]
    end = task["end"]

    for tf in task["timeframes"]:
        print(f"⬇️ Descargando {symbol} {tf}...")

        data = get_klines(symbol, tf, start, end)
        df = to_dataframe(data)

        save_csv(df, symbol, tf)

print("✅ TAREA COMPLETADA")
