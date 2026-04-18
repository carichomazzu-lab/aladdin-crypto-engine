import requests
import json
import time
import os
import pandas as pd
from datetime import datetime

# ==============================
# 1. Cargar configuración
# ==============================
with open("config.json") as f:
    config = json.load(f)

assets = config["assets"]
interval = config["interval"]

# ==============================
# 2. Crear carpeta de datos
# ==============================
if not os.path.exists("data"):
    os.makedirs("data")

# ==============================
# 3. Obtener precios (UNA sola request)
# ==============================
def get_prices_bulk(assets):
    ids = ",".join(assets)
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"
    return requests.get(url).json()

# ==============================
# 4. Guardar en JSON (tipo vault)
# ==============================
def save_json(data):
    filename = f"data/prices_{datetime.now().strftime('%Y%m%d')}.json"
    
    with open(filename, "a") as f:
        f.write(json.dumps(data) + "\n")

# ==============================
# 5. Guardar en CSV
# ==============================
def save_csv(data):
    df = pd.DataFrame([data])
    
    filename = f"data/prices_{datetime.now().strftime('%Y%m%d')}.csv"
    
    if not os.path.exists(filename):
        df.to_csv(filename, index=False)
    else:
        df.to_csv(filename, mode="a", header=False, index=False)

# ==============================
# 6. LOOP PRINCIPAL
# ==============================
while True:
    try:
        prices = get_prices_bulk(assets)
        
        for asset in assets:
            if asset in prices:
                price = prices[asset]["usd"]
                
                record = {
                    "timestamp": str(datetime.now()),
                    "asset": asset,
                    "price": price
                }

                print(f"{asset}: {price}")

                save_json(record)
                save_csv(record)

    except Exception as e:
        print("ERROR:", e)

    time.sleep(interval)