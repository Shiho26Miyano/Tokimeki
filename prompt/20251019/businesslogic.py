import os
import datetime as dt
from urllib.parse import urlencode

import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("POLYGON_API_KEY")
BASE = "https://api.polygon.io"

def get(url, params=None):
    params = params or {}
    params["apiKey"] = API_KEY
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def chain_snapshot(underlying: str) -> pd.DataFrame:
    """
    Returns a normalized DataFrame of the option chain snapshot for the underlying.
    """
    url = f"{BASE}/v3/snapshot/options/{underlying.upper()}"
    data = get(url)
    rows = []
    for c in data.get("results", []):
        day = c.get("day", {}) or {}
        greeks = c.get("greeks", {}) or {}
        rows.append({
            "contract": c.get("contract"),
            "type": c.get("details", {}).get("contract_type"),
            "strike": c.get("details", {}).get("strike_price"),
            "expiry": c.get("details", {}).get("expiration_date"),
            "iv": c.get("implied_volatility"),
            "delta": greeks.get("delta"),
            "gamma": greeks.get("gamma"),
            "theta": greeks.get("theta"),
            "vega": greeks.get("vega"),
            "last": c.get("last_quote", {}).get("p"),
            "day_volume": day.get("volume"),
            "day_oi": day.get("open_interest")
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df["expiry"] = pd.to_datetime(df["expiry"]).dt.date
        df = df.sort_values(["expiry", "strike", "type"])
    return df

def call_put_ratios(df: pd.DataFrame):
    """
    Compute call/put ratios using today's volume and open interest.
    """
    if df.empty:
        return {"volume_ratio": None, "oi_ratio": None}
    calls = df[df["type"] == "call"]
    puts = df[df["type"] == "put"]
    vol_c = calls["day_volume"].fillna(0).sum()
    vol_p = puts["day_volume"].fillna(0).sum()
    oi_c = calls["day_oi"].fillna(0).sum()
    oi_p = puts["day_oi"].fillna(0).sum()
    volume_ratio = (vol_c / vol_p) if vol_p > 0 else None
    oi_ratio = (oi_c / oi_p) if oi_p > 0 else None
    return {"volume_ratio": volume_ratio, "oi_ratio": oi_ratio}

def contract_bars_1m(contract: str, date_from: str, date_to: str) -> pd.DataFrame:
    """
    Fetch 1-minute bars for a specific option contract between date_from and date_to (YYYY-MM-DD).
    """
    path = f"/v2/aggs/t/{contract}/range/1/minute/{date_from}/{date_to}"
    url = f"{BASE}{path}"
    data = get(url, params={"adjusted": "true", "sort": "asc", "limit": 50000})
    results = data.get("results", []) or []
    if not results:
        return pd.DataFrame()
    df = pd.DataFrame(results)
    # polygon aggregates: t=ms epoch, c=close, v=volume, etc.
    df["ts"] = pd.to_datetime(df["t"], unit="ms")
    return df[["ts", "o", "h", "l", "c", "v"]].rename(columns={
        "o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"
    })

def last_n_trading_days(n=5):
    # Simple approximation: take last n+3 calendar days and sort market days.
    today = dt.date.today()
    start = today - dt.timedelta(days=n+7)
    return start.isoformat(), today.isoformat()

def main():
    ticker = "COST"
    df = chain_snapshot(ticker)
    if df.empty:
        print("No chain data returned.")
        return

    # Top by Open Interest and by Volume
    top_oi = df.sort_values("day_oi", ascending=False).head(10)
    top_vol = df.sort_values("day_volume", ascending=False).head(10)

    ratios = call_put_ratios(df)

    print(f"=== {ticker} Chain (sample) ===")
    print("Top by OI:")
    print(top_oi[["contract", "expiry", "type", "strike", "iv", "day_oi"]].to_string(index=False))
    print("\nTop by Volume:")
    print(top_vol[["contract", "expiry", "type", "strike", "iv", "day_volume"]].to_string(index=False))

    print("\nCall/Put Ratios:")
    print(f"Volume ratio (calls/puts): {ratios['volume_ratio']}")
    print(f"OI ratio (calls/puts): {ratios['oi_ratio']}")

    # Drill into the single highest-OI contract
    best = top_oi.iloc[0]
    contract = best["contract"]
    date_from, date_to = last_n_trading_days(5)
    bars = contract_bars_1m(contract, date_from, date_to)

    print(f"\n1-minute bars for highest-OI contract: {contract} [{date_from} → {date_to}]")
    if bars.empty:
        print("No bars available.")
    else:
        print(bars.tail(10).to_string(index=False))

if __name__ == "__main__":
    if not API_KEY:
        raise SystemExit("Please set POLYGON_API_KEY in your .env")
    main()
