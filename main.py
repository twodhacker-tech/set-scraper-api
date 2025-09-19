import json
import datetime
import pytz
import os
import time
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify

app = Flask(__name__)

# ---------------------- File Names ----------------------
DATA_FILE_DAILY = "DailyResult.json"      # တစ်နေ့တည်း overwrite
DATA_FILE_HISTORY = "HistoryResult.json"  # နေ့တိုင်း စုဆောင်း

# ---------------------- Load Daily Data ----------------------
def load_daily():
    try:
        with open(DATA_FILE_DAILY, "r") as f:
            return json.load(f)
    except:
        return {
            "date": "--",
            "time": "--",
            "Am": {},
            "Pm": {}
        }

# ---------------------- Save Daily (overwrite) ----------------------
def save_daily(data):
    with open(DATA_FILE_DAILY, "w") as f:
        json.dump(data, f, indent=2)

# ---------------------- Save History (append) ----------------------
def save_history(date, period, live):
    try:
        with open(DATA_FILE_HISTORY, "r") as f:
            history = json.load(f)
    except:
        history = {}

    if date not in history:
        history[date] = {}

    history[date][period] = live

    with open(DATA_FILE_HISTORY, "w") as f:
        json.dump(history, f, indent=2)

# ---------------------- Scraping ----------------------
def get_live():
    url = "https://www.set.or.th/en/market/product/stock/overview"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find_all("table")[1]
    set_index = table.find_all("div")[4]
    value_index = table.find_all("div")[6]

    live_set = set_index.get_text(strip=True)
    live_value = value_index.get_text(strip=True)

    # SET index → last digit
    clean_set = live_set.replace(",", "")
    formatted = "{:.2f}".format(float(clean_set))
    top = formatted[-1]

    # Value → last digit
    clean_value = live_value.replace(",", "")
    if clean_value in ["", "-"]:
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

# ---------------------- Date & Time ----------------------
def string_date_time():
    mm_time = datetime.datetime.now(pytz.timezone("Asia/Yangon"))
    string_date = mm_time.strftime("%Y-%m-%d")
    string_time = mm_time.strftime("%H:%M:%S")
    return {
        "date": string_date,
        "time": string_time
    }

# ---------------------- Record Live Data ----------------------
def record_live():
    now = datetime.datetime.now(pytz.timezone("Asia/Yangon"))
    string_date = now.strftime("%Y-%m-%d")
    string_time = now.strftime("%H:%M:%S")

    daily = load_daily()
    live = get_live()["live"]

    # daily overwrite
    daily["date"] = string_date
    daily["time"] = string_time

    if string_time == "12:01:00":
        daily["Am"] = live
        save_daily(daily)
        save_history(string_date, "Am", live)

    if string_time == "16:30:00":
        daily["Pm"] = live
        save_daily(daily)
        save_history(string_date, "Pm", live)
        return live

    return daily

# ---------------------- API Routes ----------------------
@app.route("/api/daily")
def api_daily():
    return jsonify(load_daily())

@app.route("/api/history")
def api_history():
    try:
        with open(DATA_FILE_HISTORY, "r") as f:
            history = json.load(f)
    except:
        history = {}
    return jsonify(history)

@app.route("/api/data")
def api_data():
    return jsonify(string_date_time(),get_live())

@app.route("/")
def root():
    return jsonify(string_date_time(),get_live())

# ---------------------- Run Server ----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)