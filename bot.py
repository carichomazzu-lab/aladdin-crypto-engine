import requests
import json
import time
from datetime import datetime

# ==============================
# CONFIGURACIÓN
# ==============================
with open("config.json") as f:
    config = json.load(f)

assets = config["assets"]
interval = config["interval"]

print("🔥 BOT ALADDIN INICIADO 🔥")

# ==============================
# HISTORIAL DE PRECIOS
# ==============================
price_history = {}

# ==============================
# OBTENER PRECIOS (COINGECKO)
# ==============================
def get_prices(assets):
    ids = ",".join(assets)
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"
    
    try:
        response = requests.get(url)
        return response.json()
    except Exception as e:
        print("ERROR API:", e)
        return {}

# ==============================
# CALCULAR MEDIA MÓVIL
# ==============================
def calculate_ma(asset, price):
    if asset not in price_history:
        price_history[asset] = []
    
    price_history[asset].append(price)

    # limitar historial a 20 datos
    if len(price_history[asset]) > 20:
        price_history[asset].pop(0)

    if len(price_history[asset]) >= 5:
        ma_5 = sum(price_history[asset][-5:]) / 5
        return ma_5
    
    return None

# ==============================
# ESTRATEGIA SIMPLE
# ==============================
def generate_signal(price, ma):
    if ma is None:
        return "WAIT"
    if price > ma:
        return "BUY"
    elif price < ma:
        return "SELL"
    return "HOLD"

# ==============================
# LOOP PRINCIPAL
# ==============================
while True:
    prices = get_prices(assets)

    for asset in assets:
        if asset in prices:
            price = prices[asset]["usd"]

            ma = calculate_ma(asset, price)
            signal = generate_signal(price, ma)

            record = {
                "timestamp": str(datetime.now()),
                "asset": asset,
                "price": price,
                "metrics": {
                    "ma_5": ma
                },
                "signal": signal,
                "source": "coingecko"
            }

            # 📡 BÓVEDA (logs estructurados)
            print(json.dumps(record))

    time.sleep(interval)
