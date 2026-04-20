import json, numpy as np, requests

API_BASE = "https://api.binance.com"
ss = requests.Session()

def get_klines(symbol, interval, limit=500):
    r = ss.get(f"{API_BASE}/api/v3/klines",
               params={"symbol": symbol, "interval": interval, "limit": limit})
    r.raise_for_status()
    return r.json()

def spot_price(symbol):
    r = ss.get(f"{API_BASE}/api/v3/ticker/price?symbol={symbol}")
    return float(r.json()["price"])

def calc_ema(arr, period):
    out = np.zeros(len(arr))
    out[0] = arr[0]
    k = 2/(period+1)
    for i in range(1,len(arr)):
        out[i] = arr[i]*k + out[i-1]*(1-k)
    return out

# ─────────────────────────────────────────────
# 🚀 ENGINE PRINCIPAL
# ─────────────────────────────────────────────

def run_strategy(slot):

    symbol = slot["symbol"]
    tf = slot["timeframe"]
    params = slot["params"]

    kl = get_klines(symbol, tf, 500)

    close = np.array([float(k[4]) for k in kl])
    high = np.array([float(k[2]) for k in kl])
    low = np.array([float(k[3]) for k in kl])
    vol = np.array([float(k[5]) for k in kl])

    idx = len(close) - 2

    if slot["strategy"] == "DONCHIAN_BREAKOUT":

        period = params["donchian_period"]
        vol_mult = params["volume_mult"]
        ema_period = params["ema_period"]
        regime_candles = params["regime_candles"]

        don_high = np.max(high[idx-period:idx])
        don_low = np.min(low[idx-period:idx])

        vol_ma = np.convolve(vol, np.ones(20)/20, mode="same")
        ema = calc_ema(close, ema_period)

        slope_ok = ema[idx] > ema[idx-3]
        over_ema = all(close[i] > ema[i] for i in range(idx-regime_candles+1, idx+1))

        regime_ok = slope_ok and over_ema

        entry = (
            close[idx] > don_high and
            vol[idx] > vol_ma[idx]*vol_mult and
            close[idx] > ema[idx] and
            regime_ok
        )

        exit = close[idx] < don_low

        return {
            "symbol": symbol,
            "entry": bool(entry),
            "exit": bool(exit),
            "price": float(close[idx])
        }

    return {"error": "strategy_not_found"}
