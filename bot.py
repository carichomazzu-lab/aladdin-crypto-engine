import requests
import json
from datetime import datetime
import pandas as pd

print("🧠 ALADDIN HISTORICAL ENGINE")

# ==============================
# CARGAR ESTRATEGIA
# ==============================
with open("strategy.json") as f:
    strategy = json.load(f)

# ==============================
# OBTENER DATOS HISTÓRICOS
# ==============================
def get_historical(strategy):
    asset = strategy["asset"]
    data_config = strategy["data"]

    if data_config["mode"] == "days":
        days = data_config["value"]

        url = f"https://api.coingecko.com/api/v3/coins/{asset}/market_chart?vs_currency=usd&days={days}"
        data = requests.get(url).json()

        prices = data["prices"]

        df = pd.DataFrame(prices, columns=["timestamp", "price"])
        df["price"] = df["price"].astype(float)

        return df

    else:
        raise Exception("Modo de datos no soportado aún")

# ==============================
# ESTRATEGIA
# ==============================
def run_strategy(df, strategy):
    params = strategy["params"]

    short = params["short_window"]
    long = params["long_window"]

    df["ma_short"] = df["price"].rolling(short).mean()
    df["ma_long"] = df["price"].rolling(long).mean()

    df["signal"] = 0
    df.loc[df["ma_short"] > df["ma_long"], "signal"] = 1
    df.loc[df["ma_short"] < df["ma_long"], "signal"] = -1

    return df

# ==============================
# EVALUACIÓN
# ==============================
def evaluate(df):
    df["returns"] = df["price"].pct_change()
    df["strategy_returns"] = df["returns"] * df["signal"].shift(1)

    total_return = df["strategy_returns"].sum()
    trades = df["signal"].abs().sum()

    win_rate = (df["strategy_returns"] > 0).sum() / len(df)

    return {
        "total_return": float(total_return),
        "trades": int(trades),
        "win_rate": float(win_rate)
    }

# ==============================
# INFORME
# ==============================
def generate_report(strategy, results):
    return {
        "timestamp": str(datetime.now()),
        "strategy": strategy,
        "results": results
    }

# ==============================
# BÓVEDA
# ==============================
def save_vault(report):
    with open("vault.json", "a") as f:
        f.write(json.dumps(report) + "\n")

    print("📦 INFORME GENERADO")
    print(json.dumps(report, indent=2))

# ==============================
# MAIN
# ==============================
df = get_historical(strategy)
df = run_strategy(df, strategy)
results = evaluate(df)

report = generate_report(strategy, results)
save_vault(report)
