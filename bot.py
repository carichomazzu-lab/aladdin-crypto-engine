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

print("🧠 ALADDIN QUANT ENGINE V9 CLEAN")

# ==============================
# LOAD CONFIG
# ==============================
with open("task.json") as f:
    task = json.load(f)

with open("strategy.json") as f:
    strategy = json.load(f)

# ==============================
# DOWNLOAD DATA
# ==============================
def download_month(symbol, interval, year, month):
    url = f"https://data.binance.vision/data/spot/monthly/klines/{symbol}/{interval}/{symbol}-{interval}-{year}-{month:02d}.zip"
    print(f"⬇️ {symbol} {interval} {year}-{month:02d}")

    r = requests.get(url)
    if r.status_code != 200:
        return None

    z = zipfile.ZipFile(io.BytesIO(r.content))
    file = z.namelist()[0]

    with z.open(file) as f:
        df = pd.read_csv(f, header=None)

    df = df.iloc[:, :6]
    df.columns = ["timestamp","open","high","low","close","volume"]

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

    df = pd.concat(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit='ms')

    for col in ["open","high","low","close","volume"]:
        df[col] = df[col].astype(float)

    return df

# ==============================
# FLEX STRATEGY ENGINE
# ==============================
def apply_strategy(df, strategy):

    name = strategy["name"]

    if name == "moving_average":
        s = strategy["params"]["short_window"]
        l = strategy["params"]["long_window"]

        df["ma_s"] = df["close"].rolling(s).mean()
        df["ma_l"] = df["close"].rolling(l).mean()

        df["signal"] = 0
        df.loc[df["ma_s"] > df["ma_l"], "signal"] = 1
        df.loc[df["ma_s"] < df["ma_l"], "signal"] = -1

    elif name == "donchian_breakout":
        n = strategy["params"]["period"]

        df["high_n"] = df["high"].rolling(n).max()
        df["low_n"] = df["low"].rolling(n).min()

        df["signal"] = 0
        df.loc[df["close"] > df["high_n"].shift(1), "signal"] = 1
        df.loc[df["close"] < df["low_n"].shift(1), "signal"] = -1

    else:
        raise Exception(f"Estrategia no soportada: {name}")

    return df

# ==============================
# METRICS
# ==============================
def evaluate(df):
    df["returns"] = df["close"].pct_change()
    df["strategy_returns"] = df["returns"] * df["signal"].shift(1)

    gains = df[df["strategy_returns"] > 0]["strategy_returns"].sum()
    losses = abs(df[df["strategy_returns"] < 0]["strategy_returns"].sum())

    pf = gains / losses if losses != 0 else 0

    cumulative = (1 + df["strategy_returns"]).cumprod()
    peak = cumulative.cummax()
    dd = (cumulative - peak) / peak

    return {
        "return": float(df["strategy_returns"].sum()),
        "profit_factor": float(pf),
        "max_drawdown": float(dd.min())
    }

# ==============================
# MAIN
# ==============================
report = {
    "time": str(datetime.now()),
    "results": {}
}

for symbol in task["symbols"]:
    for interval in task["intervals"]:

        df = download_range(symbol, interval, task["start"], task["end"])
        df = apply_strategy(df, strategy)

        metrics = evaluate(df)

        key = f"{symbol}_{interval}"
        report["results"][key] = metrics

with open("report.json", "w") as f:
    json.dump(report, f, indent=2)

print("\n📦 REPORTE GENERADO")
print("🏁 FIN")
