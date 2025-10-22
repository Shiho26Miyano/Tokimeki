"""
Goal:
Generate two front end chart based on the logic of python Matplotlib charts from my options chain data:
1. Open Interest Change Heatmap (ΔOI)
2. Delta Distribution Histogram

Input:
A DataFrame `df` with columns:
['expiry', 'strike', 'type', 'oi_today', 'oi_yesterday', 'delta', 'volume']

Behavior:
- Each expiry has multiple strikes.
- Calls and puts both included.
"""


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ---------- 1. Open Interest Change Heatmap ----------
def plot_oi_change(df):
    expiries = sorted(df["expiry"].unique())
    strikes = sorted(df["strike"].unique())

    grid = df.pivot_table(
        index="expiry", columns="strike",
        values="oi_today", aggfunc="sum"
    ).reindex(index=expiries, columns=strikes).fillna(0)
    grid_y = df.pivot_table(
        index="expiry", columns="strike",
        values="oi_yesterday", aggfunc="sum"
    ).reindex(index=expiries, columns=strikes).fillna(0)

    delta_oi = grid - grid_y

    fig, ax = plt.subplots(figsize=(5, 3))
    im = ax.imshow(delta_oi, aspect="auto", cmap="viridis", origin="lower")
    ax.set_xticks(np.arange(len(strikes)))
    ax.set_xticklabels(strikes, rotation=45)
    ax.set_yticks(np.arange(len(expiries)))
    ax.set_yticklabels([pd.to_datetime(e).strftime('%m-%d') for e in expiries])
    ax.set_xlabel("Strike")
    ax.set_ylabel("Expiry")
    ax.set_title("Open Interest Change")
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Δ OI (contracts)")
    plt.tight_layout()
    plt.show()

# ---------- 2. Delta Distribution ----------
def plot_delta_distribution(df):
    deltas = df["delta"].dropna().clip(-1, 1)
    weights = df["volume"].fillna(1)
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.hist(deltas, bins=np.linspace(-1, 1, 21),
            weights=weights, color="#ff7f0e", edgecolor="white", linewidth=0.5)
    ax.set_title("Delta Distribution")
    ax.set_xlabel("Delta")
    ax.set_ylabel("Contracts (weighted)")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

# Example usage:
# df = polygon_chain_to_df(ticker="COST")
# plot_oi_change(df)
# plot_delta_distribution(df)