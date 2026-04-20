<<<<<<< HEAD
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
=======
import requests
import zipfile
import io
import pandas as pd
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# ==============================
# INIT
# ==============================
load_dotenv()
API_KEY = os.getenv("ALADINO")

print("🧠 ALADDIN QUANT ENGINE PRO V9 (CACHE + CONTROL)")

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# ==============================
# LOAD FILES
# ==============================
with open("task.json") as f:
    task = json.load(f)

with open("strategy.json") as f:
    strategy = json.load(f)

# ==============================
# DOWNLOAD + CACHE
# ==============================
def get_local_filename(symbol, interval, year, month):
    return f"{DATA_DIR}/{symbol}_{interval}_{year}_{month:02d}.csv"

def download_month(symbol, interval, year, month):

    filename = get_local_filename(symbol, interval, year, month)

    # ✅ CACHE
    if os.path.exists(filename):
        print(f"📂 CACHE {symbol} {interval} {year}-{month:02d}")
        return pd.read_csv(filename)

    url = f"https://data.binance.vision/data/spot/monthly/klines/{symbol}/{interval}/{symbol}-{interval}-{year}-{month:02d}.zip"

    print(f"⬇️ {symbol} {interval} {year}-{month:02d}")

    r = requests.get(url)
    if r.status_code != 200:
        return None

    z = zipfile.ZipFile(io.BytesIO(r.content))
    file = z.namelist()[0]

    with z.open(file) as f:
        df = pd.read_csv(f, header=None)

    df = df.iloc[:, :12]

    df.columns = [
        "timestamp","open","high","low","close","volume",
        "close_time","qav","trades","tbbav","tbqav","ignore"
    ]

    df.to_csv(filename, index=False)

    return df

def download_range(symbol, interval, start, end):

    data = []
    y, m = start["year"], start["month"]

    while (y < end["year"]) or (y == end["year"] and m <= end["month"]):
        df = download_month(symbol, interval, y, m)

        if df is not None:
            data.append(df)

        m += 1
        if m > 12:
            m = 1
            y += 1

    if not data:
        raise Exception(f"No data {symbol} {interval}")

    df = pd.concat(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit='ms')

    for col in ["open","high","low","close","volume"]:
        df[col] = df[col].astype(float)

    return df

# ==============================
# STRATEGY ENGINE
# ==============================
def apply_strategy(df, strategy):

    strat_type = strategy["type"]

    if strat_type == "moving_average":
        s = strategy["params"]["short_window"]
        l = strategy["params"]["long_window"]

        df["ma_short"] = df["close"].rolling(s).mean()
        df["ma_long"] = df["close"].rolling(l).mean()

        df["signal"] = 0
        df.loc[df["ma_short"] > df["ma_long"], "signal"] = 1
        df.loc[df["ma_short"] < df["ma_long"], "signal"] = -1

    elif strat_type == "donchian":

        period = strategy["params"]["donchian_period"]
        vol_mult = strategy["params"]["vol_mult"]

        df["donchian_high"] = df["high"].rolling(period).max().shift(1)
        df["donchian_low"] = df["low"].rolling(period).min().shift(1)
        df["vol_ma"] = df["volume"].rolling(20).mean()

        df["signal"] = 0

        df.loc[
            (df["close"] > df["donchian_high"]) &
            (df["volume"] > df["vol_ma"] * vol_mult),
            "signal"
        ] = 1

        df.loc[df["close"] < df["donchian_low"], "signal"] = -1

    else:
        raise Exception(f"Estrategia no soportada: {strat_type}")

    return df

# ==============================
# METRICS
# ==============================
def evaluate(df):

    df["returns"] = df["close"].pct_change()
    df["strategy_returns"] = df["returns"] * df["signal"].shift(1)
    df = df.dropna()

    gains = df[df["strategy_returns"] > 0]["strategy_returns"].sum()
    losses = abs(df[df["strategy_returns"] < 0]["strategy_returns"].sum())

    pf = gains / losses if losses != 0 else 0

    cumulative = (1 + df["strategy_returns"]).cumprod()
    peak = cumulative.cummax()
    dd = (cumulative - peak) / peak

    return {
        "total_return": float(df["strategy_returns"].sum()),
        "profit_factor": float(pf),
        "max_drawdown": float(dd.min())
    }

# ==============================
# MAIN
# ==============================
report = {
    "timestamp": str(datetime.now()),
    "strategy": strategy,
    "results": {}
}

symbols = task.get("symbols", [task.get("symbol")])

for symbol in symbols:
    report["results"][symbol] = {}

    for interval in task["intervals"]:

        df = download_range(symbol, interval, task["start"], task["end"])
        df = apply_strategy(df, strategy)

        metrics = evaluate(df)

        df.to_csv(f"{DATA_DIR}/FINAL_{symbol}_{interval}.csv", index=False)
        report["results"][symbol][interval] = metrics

# ==============================
# SAVE
# ==============================
with open("report.json", "w") as f:
    json.dump(report, f, indent=2)

print("\n📦 REPORTE GENERADO")
print("🏁 FIN")
>>>>>>> aa5fe46 (Aladdin engine)
