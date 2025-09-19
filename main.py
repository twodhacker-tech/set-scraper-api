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

# ---------------------- Helpers: load/save ----------------------
def load_daily():
    try:
        with open(DATA_FILE_DAILY, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading daily data: {e}")
        return {
            "date": "--",
            "time": "--",
            "Am": {},
            "Pm": {}
        }

def save_daily(data):
    try:
        with open(DATA_FILE_DAILY, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving daily data: {e}")

def load_history():
    try:
        with open(DATA_FILE_HISTORY, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading history data: {e}")
        return {}

def save_history(date_str, period, live):
    try:
        history = load_history()
        if date_str not in history:
            history[date_str] = {}
        history[date_str][period] = live
        with open(DATA_FILE_HISTORY, "w") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving history data: {e}")

# ---------------------- Scraping / Live ----------------------
def get_live():
    """
    Returns live data such as stock market details.
    """
    url = "https://www.set.or.th/en/market/product/stock/overview"
    fetched_at = int(time.time())
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        return {"live": {"twod": "", "set": "", "value": "", "fetched_at": fetched_at, "error": f"request_error: {e}"}}

    soup = BeautifulSoup(resp.text, "html.parser")
    try:
        tables = soup.find_all("table")
        table = tables[1]  # site structure dependent
        divs = table.find_all("div")
        set_index = divs[4]
        value_index = divs[6]

        live_set = set_index.get_text(strip=True)
        live_value = value_index.get_text(strip=True)

        # last digit from set
        clean_set = live_set.replace(",", "")
        formatted = "{:.2f}".format(float(clean_set))
        top = formatted[-1]

        # last digit from value
        clean_value = live_value.replace(",", "")
        if clean_value in ["", "-"]:
            clean_value = "0.00"
        last = str(int(float(clean_value)))[-1]

        twod_live = f"{top}{last}"

        return {"live": {"twod": twod_live, "set": live_set, "value": live_value, "fetched_at": fetched_at}}
    except Exception as e:
        return {"live": {"twod": "", "set": "", "value": "", "fetched_at": fetched_at, "error": f"parse_error: {e}"}}

# ---------------------- Server time helper ----------------------
def string_date_time():
    mm_time = datetime.datetime.now(pytz.timezone("Asia/Yangon"))
    return {
        "date": mm_time.strftime("%Y-%m-%d"),
        "time": mm_time.strftime("%H:%M:%S")
    }

# ---------------------- Record Live Data ----------------------
def record_live():
    """
    Record live data into daily and history files for AM and PM.
    """
    now = datetime.datetime.now(pytz.timezone("Asia/Yangon"))
    string_date = now.strftime("%Y-%m-%d")
    string_time = now.strftime("%H:%M:%S")

    daily = load_daily()
    live_obj = get_live().get("live", {})
    # update daily meta
    daily["date"] = string_date
    daily["time"] = string_time

    result = {"date": string_date, "time": string_time, "saved": False, "period": None, "live": live_obj}

    if string_time == "12:01:00":
        daily["Am"] = live_obj
        save_daily(daily)
        save_history(string_date, "Am", live_obj)
        result.update({"saved": True, "period": "Am"})
        return result

    if string_time == "16:30:00":
        daily["Pm"] = live_obj
        save_daily(daily)
        save_history(string_date, "Pm", live_obj)
        result.update({"saved": True, "period": "Pm"})
        return result

    # If not the exact times, just update daily (not saving Am/Pm)
    save_daily(daily)  # optional: keep daily meta always up-to-date
    return result

# ---------------------- API Routes ----------------------
@app.route("/api/all")
def api_all():
    """
    Endpoint to return live data, daily, and history
    """
    # Load live, daily, and history data
    live = get_live().get("live", {})
    daily = load_daily()
    history = load_history()

    # Ensure the response is a single object
    response = {
        "live": live,
        "daily": daily,
        "history": history,
        "server_time": string_date_time()  # Include the server time as well
    }

    return jsonify(response)

@app.route("/api/daily")
def api_daily():
    return jsonify(load_daily())

@app.route("/api/history")
def api_history():
    return jsonify(load_history())

@app.route("/api/data")
def api_data():
    return jsonify(string_date_time(),get_live(),record_live())

@app.route("/")
def root():
    return jsonify(string_date_time(),get_live(),record_live())

@app.route("/api/record", methods=["GET", "POST"])
def api_record():
    """
    Manually trigger the record live data function.
    """
    res = record_live()
    return jsonify(res)

# ---------------------- Run Server ----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)