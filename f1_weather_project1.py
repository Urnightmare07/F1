import os
import subprocess
import requests
from dotenv import load_dotenv
import pandas as pd
from fastf1 import get_session
from datetime import timedelta, datetime
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from tableauhyperapi import (
    HyperProcess, Connection, TableDefinition, SqlType, TableName, Inserter,
    Telemetry, CreateMode, NOT_NULLABLE, NULLABLE
)
import google.generativeai as genai


# === Load API Key ===
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("Missing GOOGLE_API_KEY in .env file")

# === Configure Gemini ===
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.5-pro")


# === Open-Meteo Real-Time + Forecast Connector ===
def get_weather_forecast(lat, lon, hours=3):
    """
    Fetch live + hourly forecast weather data from Open-Meteo.
    Returns current snapshot and next {hours} hours forecast.
    """
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current_weather=true"
        f"&hourly=temperature_2m,relative_humidity_2m,windspeed_10m,precipitation"
    )
    resp = requests.get(url).json()

    # Current snapshot
    current = resp["current_weather"]
    snapshot = {
        "temp": current["temperature"],
        "wind_speed": current["windspeed"],
        "rain": current.get("precipitation", 0) > 0,
        "time": current["time"]
    }

    # Forecast (hourly)
    forecast_df = pd.DataFrame({
        "time": resp["hourly"]["time"],
        "temp": resp["hourly"]["temperature_2m"],
        "rhum": resp["hourly"]["relative_humidity_2m"],
        "wind_speed": resp["hourly"]["windspeed_10m"],
        "precip": resp["hourly"]["precipitation"]
    })
    forecast_df["rain"] = forecast_df["precip"] > 0

    # Only next N hours
    forecast_df["time"] = pd.to_datetime(forecast_df["time"])
    now = pd.to_datetime(snapshot["time"])
    forecast_df = forecast_df[(forecast_df["time"] >= now) &
                              (forecast_df["time"] <= now + timedelta(hours=hours))]

    return snapshot, forecast_df


# === Tableau Hyper Export ===
def export_to_hyper(df, hyper_path):
    """Export DataFrame to Tableau .hyper format with schema creation."""
    with HyperProcess(telemetry=Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper:
        with Connection(endpoint=hyper.endpoint, database=hyper_path,
                        create_mode=CreateMode.CREATE_AND_REPLACE) as connection:

            connection.catalog.create_schema('Extract')

            table_def = TableDefinition(
                TableName("Extract", "Extract"),
                columns=[
                    TableDefinition.Column("LapNumber", SqlType.int(), NOT_NULLABLE),
                    TableDefinition.Column("Driver", SqlType.text(), NOT_NULLABLE),
                    TableDefinition.Column("LapTimeSeconds", SqlType.double(), NULLABLE),
                    TableDefinition.Column("temp", SqlType.double(), NULLABLE),
                    TableDefinition.Column("rhum", SqlType.double(), NULLABLE),
                    TableDefinition.Column("wspd", SqlType.double(), NULLABLE),
                    TableDefinition.Column("Rain", SqlType.bool(), NOT_NULLABLE),
                    TableDefinition.Column("KMeans_Cluster", SqlType.int(), NULLABLE),
                    TableDefinition.Column("DBSCAN_Cluster", SqlType.int(), NULLABLE)
                ]
            )

            connection.catalog.create_table(table_def)

            with Inserter(connection, table_def) as inserter:
                for _, row in df.iterrows():
                    inserter.add_row([
                        int(row["LapNumber"]),
                        str(row["Driver"]),
                        float(row["LapTimeSeconds"]) if pd.notnull(row["LapTimeSeconds"]) else None,
                        float(row["temp"]) if pd.notnull(row["temp"]) else None,
                        float(row["rhum"]) if pd.notnull(row["rhum"]) else None,
                        float(row["wspd"]) if pd.notnull(row["wspd"]) else None,
                        bool(row["Rain"]),
                        int(row["KMeans_Cluster"]) if pd.notnull(row["KMeans_Cluster"]) else None,
                        int(row["DBSCAN_Cluster"]) if pd.notnull(row["DBSCAN_Cluster"]) else None
                    ])
                inserter.execute()


# === F1 + Weather Analysis and Clustering ===
def analyze():
    year, gp_name, session_type = 2023, "Zandvoort", "R"
    session = get_session(year, gp_name, session_type)
    session.load()

    # Circuit coordinates (Zandvoort)
    lat, lon = 52.3888, 4.5409

    # --- Live Weather + Forecast (Open-Meteo) ---
    live_weather, forecast_df = get_weather_forecast(lat, lon, hours=3)
    print("\n🌦 Live Weather Snapshot:", live_weather)
    print("\n📅 Next 3h Forecast:")
    print(forecast_df.head())

    # --- Lap Data ---
    try:
        session_start = session.session_start_time.to_pydatetime()
    except:
        session_start = datetime(year, 8, 27, 14)

    laps = session.laps.copy()
    laps["LapStartTime"] = (session_start + laps["LapStartTime"]).dt.round("min")

    # Attach live weather values to each lap
    laps["temp"] = live_weather["temp"]
    laps["rhum"] = 60.0  # Placeholder (humidity forecast used only in forecast_df)
    laps["wspd"] = live_weather["wind_speed"]
    laps["Rain"] = live_weather["rain"]
    laps["LapTimeSeconds"] = laps["LapTime"].dt.total_seconds()

    # --- Clustering ---
    cluster_data = laps.dropna(subset=["LapTimeSeconds", "temp", "rhum", "wspd"]).copy()
    scaled = StandardScaler().fit_transform(cluster_data[["LapTimeSeconds", "temp", "rhum", "wspd"]])

    cluster_data["KMeans_Cluster"] = KMeans(n_clusters=3, random_state=42).fit_predict(scaled)
    cluster_data["DBSCAN_Cluster"] = DBSCAN(eps=1.0, min_samples=5).fit_predict(scaled)

    merged = laps.merge(
        cluster_data[["LapNumber", "Driver", "KMeans_Cluster", "DBSCAN_Cluster"]],
        on=["LapNumber", "Driver"],
        how="left"
    )

    # --- Summary Stats ---
    avg_dry = merged[~merged["Rain"]]["LapTimeSeconds"].mean()
    avg_wet = merged[merged["Rain"]]["LapTimeSeconds"].mean()

    # --- Save Outputs ---
    csv_path = f"f1_{year}_{gp_name}_live_weather_analysis.csv"
    hyper_path = f"f1_{year}_{gp_name}_live_weather_analysis.hyper"

    merged.to_csv(csv_path, index=False)
    export_to_hyper(merged, hyper_path)
    print(f"\n✅ Data successfully exported to {hyper_path}")

    # --- AI Strategy Summary ---
    forecast_summary = forecast_df.to_dict(orient="records")
    prompt = f"""
    The race was held at {gp_name} in {year}. 
    Current live weather: {live_weather}.
    Forecast for the next 3 hours: {forecast_summary}.
    - Average dry lap time: {avg_dry:.3f} seconds
    - Average wet lap time: {avg_wet:.3f} seconds
    - Clusters were formed based on lap time, air temp, humidity, and wind speed.

    Suggest pit strategies considering both current and forecast weather.
    """
    try:
        response = model.generate_content(prompt)
        print("\n=== GEMINI STRATEGY SUMMARY ===")
        print(response.text)
    except Exception as e:
        print("⚠ Gemini API error:", e)

    # --- Open Tableau Desktop 2024.3 ---
    tableau_exe = r"C:\Program Files\Tableau\Tableau 2024.3\bin\tableau.exe"
    if os.path.exists(tableau_exe):
        subprocess.Popen([tableau_exe, hyper_path])
    else:
        print("⚠ Tableau 2024.3 executable not found. Please check the path.")


if __name__ == "__main__":
    analyze()
