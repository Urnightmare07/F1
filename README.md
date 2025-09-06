# F1
passioan project

# 🏎️ F1 Weather & Strategy Analysis with Tableau + Gemini AI

This project analyzes Formula 1 race data (lap times, drivers, tire/weather conditions) and combines it with **real-time weather** information to generate insights about **pit strategies and tire choices**.  
The processed data is exported into a `.hyper` file for visualization in **Tableau Desktop**, and **Google Gemini AI** is used to summarize strategy patterns.

---

## 🚀 Features
- Fetches **F1 lap data** via [FastF1](https://theoehrly.github.io/Fast-F1/).
- Collects **historical & live weather data** using [Meteostat](https://dev.meteostat.net/).
- Performs **clustering analysis** (KMeans + DBSCAN) on lap times vs weather variables.
- Exports results to:
  - **CSV** (for backup/inspection).
  - **Hyper Extract (`.hyper`)** for Tableau Desktop 2024.3.
- Opens Tableau automatically for instant visualization.
- Uses **Gemini 2.5 Pro** to generate a **strategy summary** (pit stops, tire decisions, outlier analysis).

---

## 🛠️ Installation

1. Clone or download this repo.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt

   The script will:

Download F1 session data + weather data.

Run clustering analysis.

Save results:

f1_<year>_<gp_name>_live_weather_analysis.csv

f1_<year>_<gp_name>_live_weather_analysis.hyper

Launch Tableau Desktop automatically with the .hyper file.

Print a Gemini-generated strategy summary in your terminal.

📊 Tableau Integration

The .hyper file is a data extract.

Open it directly in Tableau (os.startfile does this automatically).

You can build dashboards showing:

Lap times vs weather.

Clustered performance groups.

Dry vs wet strategy comparisons.

Real-time tire recommendations.

⚡ Example Output
=== GEMINI STRATEGY SUMMARY ===
Pit Strategy: This is purely a reactive survival situation. 
The data reinforces the need for excellent real-time weather monitoring. 
A team with superior weather forecasts can make proactive tire decisions 
that avoid poor-performing clusters entirely.

🧩 Project Structure
📂 F1-Weather-Strategy
 ┣ 📜 f1_weather_project.py   # Main Python script
 ┣ 📜 requirements.txt        # Dependencies
 ┣ 📜 .env                    # API keys (not committed to GitHub)
 ┣ 📜 README.md               # Project documentation
 ┗ 📊 f1_2023_Zandvoort_live_weather_analysis.hyper  # Example Tableau Extract

📌 Notes

By default, the script uses Zandvoort 2023 Race (R) as an example.
You can change:

year, gp_name, session_type = 2023, "Zandvoort", "R"


Supported session_type: "R" (Race), "Q" (Qualifying), "FP1", "FP2", "FP3".
