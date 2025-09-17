import json
import datetime
import pytz
import os
import time
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify

app = Flask(__name__)

DATA_FILE = "ResultsHistory.json"

# Load the data from the JSON file or initialize if not available
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Initialize with default values if file doesn't exist or is corrupted
        return {
            "date": "--",
            "time": "--",
            "live": {},
            "12:01": {},
            "4:30": {}
        }

# Save the data to the JSON file
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Scrape live data from the website
def get_live():
    url = "https://www.set.or.th/en/market/product/stock/overview"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find_all("table")[1]
    set_index = table.find_all("div")[4]
    value_index = table.find_all("div")[6]

    live_set = set_index.get_text(strip=True)
    live_value = value_index.get_text(strip=True)

    clean_set = live_set.replace(",", "")
    formatted = "{:.2f}".format(float(clean_set))
    top = formatted[-1]

    clean_value = live_value.replace(",", "")
    if clean_value in ["", "-"]:  # If data is missing, set to 0.00
        clean_value = "0.00"
    last = str(int(float(clean_value)))[-1]

    twod_live = f"{top}{last}"
    return {
        "live": {
            "twod": twod_live,
            "set": live_set,
            "value": live_value,
            "fetched_at": int(time.time())
        }
    }

# Get the current date and time in the specified timezone
def string_date_time():
    mm_time = datetime.datetime.now(pytz.timezone("Asia/Yangon"))
    string_date = mm_time.strftime("%Y-%m-%d")
    string_time = mm_time.strftime("%H:%M:%S")
    return {"date": string_date, "time": string_time}

# Record live data at specific times (12:01 and 16:30)
def record_live():
    now = datetime.datetime.now(pytz.timezone("Asia/Yangon")).strftime("%H:%M")
    data = load_data()
    live = get_live()

    # Check for specific times
    for t in ["12:01", "16:30"]:
        if now == t:
            data[t] = live["live"]
            save_data(data)
            return data
    
    # Return the data even if the time doesn't match
    return data

# API route to fetch live data
@app.route("/api/data")
def api_data():
    return jsonify(record_live())

# Root route to fetch date, time, and live data
@app.route("/")
def root():
    return jsonify({
        **string_date_time(),
        **get_live(),
        **record_live()
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)