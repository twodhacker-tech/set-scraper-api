import atexit
import datetime
import pytz
import os
import time
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import yaml

app = Flask(__name__)

# ---------------------- File Names ----------------------
DAILY_FILE = "DailyResult.yml"
HISTORY_FILE = "HistoryResult.yml"

# ---------------------- Helpers: load/save YAML ----------------------
def load_daily():
    try:
        with open(DAILY_FILE, "r") as f:
            data = yaml.safe_load(f)
            if data is None:
                data = {"date": "--", "time": "--", "Am": {}, "Pm": {}}
            return data
    except Exception as e:
        print(f"[load_daily] {e}")
        return {"date": "--", "time": "--", "Am": {}, "Pm": {}}

def save_daily(data):
    try:
        with open(DAILY_FILE, "w") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
    except Exception as e:
        print(f"[save_daily] {e}")

def load_history():
    try:
        with open(HISTORY_FILE, "r") as f:
            data = yaml.safe_load(f)
            if data is None:
                data = {}
            return data
    except Exception as e:
        print(f"[load_history] {e}")
        return {}

def save_history(date_str, period, live):
    try:
        history = load_history()
        if date_str not in history:
            history[date_str] = {}
        history[date_str][period] = live
        with open(HISTORY_FILE, "w") as f:
            yaml.safe_dump(history, f, sort_keys=False, allow_unicode=True)
    except Exception as e:
        print(f"[save_history] {e}")

# ---------------------- Scraping / Live ----------------------
def get_live():
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

        clean_set = live_set.replace(",", "")
        formatted = "{:.2f}".format(float(clean_set))
        top = formatted[-1]

        clean_value = live_value.replace(",", "")
        if clean_value in ["", "-"]:
            clean_value = "0.00"
        last = str(int(float(clean_value)))[-1]

        twod_live = f"{top}{last}"

        return {"live": {"twod": twod_live, "set": live_set, "value": live_value, "fetched_at": fetched_at}}
    except Exception as e:
        return {"live": {"twod": "", "set": "", "value": "", "fetched_at": fetched_at, "error": f"parse_error: {e}"}}

# ---------------------- Server time ----------------------
def string_date_time():
    now = datetime.datetime.now(pytz.timezone("Asia/Yangon"))
    return {"date": now.strftime("%Y-%m-%d"), "time": now.strftime("%H:%M:%S")}

# ---------------------- Record Live Data ----------------------
def record_live():
    now = datetime.datetime.now(pytz.timezone("Asia/Yangon"))
    string_date = now.strftime("%Y-%m-%d")
    string_time = now.strftime("%H:%M:%S")

    daily = load_daily()
    live_obj = get_live().get("live", {})
    daily["date"] = string_date
    daily["time"] = string_time

    result = {"date": string_date, "time": string_time, "saved": False, "period": None, "live": live_obj}

    try:
        if string_time == "12:01:00":
            daily["Am"] = live_obj
            save_daily(daily)
            save_history(string_date, "Am", live_obj)
            result.update({"saved": True, "period": "Am"})
            print(f"[record_live] Saved AM for {string_date} at {string_time}")
            return result

        if string_time == "16:30:00":
            daily["Pm"] = live_obj
            save_daily(daily)
            save_history(string_date, "Pm", live_obj)
            result.update({"saved": True, "period": "Pm"})
            print(f"[record_live] Saved PM for {string_date} at {string_time}")
            return result

        save_daily(daily)  # update daily meta
        print(f"[record_live] Updated daily meta for {string_date} at {string_time}")
        return result
    except Exception as e:
        print(f"[record_live] Error: {e}")
        result["error"] = str(e)
        return result

# ---------------------- Scheduler ----------------------
yangon_tz = pytz.timezone("Asia/Yangon")
scheduler = BackgroundScheduler(timezone=yangon_tz)

scheduler.add_job(lambda: record_live(), 'cron', hour=12, minute=1, id="save_am", max_instances=1)
scheduler.add_job(record_live, 'interval', minutes=1)
scheduler.add_job(lambda: record_live(), 'cron', hour=16, minute=30, id="save_pm", max_instances=1)

import atexit
atexit.register(lambda: scheduler.shutdown(wait=False))

# ---------------------- API Routes ----------------------
@app.route("/api/all")
def api_all():
    live = get_live().get("live", {})
    daily = load_daily()
    history = load_history()
    server_time = string_date_time()
    return jsonify({"live": live, "daily": daily, "history": history, "server_time": server_time})

@app.route("/api/daily")
def api_daily():
    return jsonify({"daily": load_daily()})

@app.route("/api/history")
def api_history():
    return jsonify({"history": load_history()})

@app.route("/api/data")
def api_data():
    live = get_live().get("live", {})
    daily = load_daily()
    history = load_history()
    server_time = string_date_time()
    return jsonify({"server_time": server_time, "live": live, "daily": daily, "history": history})

@app.route("/")
def root():
    live = get_live().get("live", {})
    daily = load_daily()
    history = load_history()
    server_time = string_date_time()
    return jsonify({"server_time": server_time, "live": live, "daily": daily, "history": history})

@app.route("/api/record", methods=["GET", "POST"])
def api_record():
    res = record_live()
    return jsonify(res)

# ---------------------- Run Server ----------------------
if __name__ == "__main__":
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        scheduler.start()
        print("[scheduler] Started (Asia/Yangon)")

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)