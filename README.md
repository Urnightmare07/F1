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
