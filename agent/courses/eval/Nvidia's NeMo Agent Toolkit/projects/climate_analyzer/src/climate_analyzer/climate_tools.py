"""Standalone climate analysis functions (course L3 Part 1).

普通 Python 函数,对 NAT 一无所知:单一职责、返回 JSON、docstring 写清用途。
注册成 NAT 工具的代码见 climate_analyzer.py。
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

DATA_PATH = Path(__file__).parent / "data" / "temperature_annual.csv"


def load_climate_data(path=DATA_PATH) -> pd.DataFrame:
    """Load NOAA-style annual temperature anomaly records from CSV.

    Columns: year, country_name, temperature_anomaly (°C vs 20th-century avg),
    num_stations.
    """
    return pd.read_csv(path)


def calculate_statistics(df: pd.DataFrame, country: str | None = None,
                         start_year: int | None = None, end_year: int | None = None) -> str:
    """Calculate temperature statistics globally or for a specific country,
    optionally limited to a year range.

    Returns JSON with mean/min/max temperature anomaly (°C), std deviation,
    record count, warming trend per decade (°C/decade) and years analyzed.
    """
    data = df if country is None else df[df["country_name"] == country]
    if start_year is not None:
        data = data[data["year"] >= start_year]
    if end_year is not None:
        data = data[data["year"] <= end_year]
    if data.empty:
        return json.dumps({"error": f"no data found for country {country}"})
    yearly = data.groupby("year")["temperature_anomaly"].mean()
    # 单条记录算不出离散度和趋势:返回 null(None),不能让 NaN 混进 JSON
    multi = len(data) >= 2
    trend = np.polyfit(yearly.index, yearly.values, 1)[0] * 10 if len(yearly) >= 2 else None
    return json.dumps({
        "country": country or "global",
        "mean_temperature": round(float(data["temperature_anomaly"].mean()), 3),
        "min_temperature": round(float(data["temperature_anomaly"].min()), 3),
        "max_temperature": round(float(data["temperature_anomaly"].max()), 3),
        "std_deviation": round(float(data["temperature_anomaly"].std()), 3) if multi else None,
        "num_records": int(len(data)),
        "trend_per_decade": round(float(trend), 3) if trend is not None else None,
        "years_analyzed": f"{int(data['year'].min())}-{int(data['year'].max())}",
    })


def filter_by_country(df: pd.DataFrame, country: str) -> str:
    """Get dataset coverage for one country: record count, station count, year range.

    Returns JSON. Use list_countries first if unsure about the exact name.
    """
    data = df[df["country_name"] == country]
    if data.empty:
        return json.dumps({"error": f"no data found for country {country}"})
    return json.dumps({
        "country": country,
        "num_records": int(len(data)),
        "num_stations": int(data["num_stations"].iloc[-1]),
        "years_covered": f"{int(data['year'].min())}-{int(data['year'].max())}",
    })


def find_extreme_years(df: pd.DataFrame, country: str | None = None, top_n: int = 5) -> str:
    """Find the warmest and coldest years on record, globally or per country.

    Returns JSON with two ranked lists of {year, temperature_anomaly}.
    """
    data = df if country is None else df[df["country_name"] == country]
    if data.empty:
        return json.dumps({"error": f"no data found for country {country}"})
    yearly = data.groupby("year")["temperature_anomaly"].mean().round(3)
    return json.dumps({
        "country": country or "global",
        "warmest_years": [{"year": int(y), "temperature_anomaly": t}
                          for y, t in yearly.nlargest(top_n).items()],
        "coldest_years": [{"year": int(y), "temperature_anomaly": t}
                          for y, t in yearly.nsmallest(top_n).items()],
    })


def create_visualization(df: pd.DataFrame, plot_type: str = "annual_trend",
                         save_path: str = "climate_plot.png") -> str:
    """Create a chart and save it as a PNG file.

    plot_type "annual_trend": global mean anomaly per year (line chart).
    plot_type "country_trends": warming trend per decade for the top-5
    fastest-warming countries (bar chart).
    Returns JSON confirming the saved file path.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 5))
    if plot_type == "country_trends":
        trends = {}
        for country, group in df.groupby("country_name"):
            yearly = group.groupby("year")["temperature_anomaly"].mean()
            trends[country] = np.polyfit(yearly.index, yearly.values, 1)[0] * 10
        top = dict(sorted(trends.items(), key=lambda kv: kv[1], reverse=True)[:5])
        ax.bar(top.keys(), top.values(), color="#d1495b")
        ax.set_ylabel("Warming trend (°C / decade)")
        ax.set_title("Top-5 fastest-warming countries")
        plt.xticks(rotation=20)
    else:
        yearly = df.groupby("year")["temperature_anomaly"].mean()
        ax.plot(yearly.index, yearly.values, color="#00798c")
        ax.set_xlabel("Year")
        ax.set_ylabel("Temperature anomaly (°C)")
        ax.set_title("Global annual temperature anomaly")
    fig.tight_layout()
    fig.savefig(save_path, dpi=120)
    plt.close(fig)
    return json.dumps({"status": "saved", "plot_type": plot_type, "file": str(save_path)})


def list_countries(df: pd.DataFrame) -> str:
    """List all countries available in the dataset. Returns a JSON array."""
    return json.dumps(sorted(df["country_name"].unique().tolist()))


def station_statistics(df: pd.DataFrame) -> str:
    """Get weather station statistics across all countries.

    Returns JSON with total_stations, countries_with_most_stations (top 5)
    and the full stations_per_country breakdown.
    """
    per_country = (df.groupby("country_name")["num_stations"].last()
                   .sort_values(ascending=False))
    return json.dumps({
        "total_stations": int(per_country.sum()),
        "countries_with_most_stations": [
            {"country": c, "num_stations": int(n)} for c, n in per_country.head(5).items()],
        "stations_per_country": {c: int(n) for c, n in per_country.items()},
    })
