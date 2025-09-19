import atexit
import json
import datetime
import pytz
import os
import time
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# ---------------------- File Names ----------------------
DATA_FILE_DAILY = "DailyResult.json"      # overwrite for today's data
DATA_FILE_HISTORY = "HistoryResult.json"  # accumulate history by date

# ---------------------- Helpers: load/save ----------------------
def load_daily():
    try:
        with open(DATA_FILE_DAILY, "r") as f:
            data = json.load(f)
            return data
    except Exception as e:
        print(f"[load_daily] Error loading daily data: {e}")
        return {"date": "--", "time": "--", "Am": {}, "Pm": {}}

def save_daily(data):
    try:
        with open(DATA_FILE_DAILY, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[save_daily] Error saving daily data: {e}")

def load_history():
    try:
        with open(DATA_FILE_HISTORY, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"[load_history] Error loading history data: {e}")
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
        print(f"[save_history] Error saving history data: {e}")

# ---------------------- Scraping / Live ----------------------
def get_live():
    """
    Returns dict: {"live": {"twod": "...", "set": "...", "value": "...", "fetched_at": ...}}
    On error returns a live dict with error key.
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
        table = tables[1]  # site structure dependent; adjust index if site layout changes
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
    return {"date": mm_time.strftime("%Y-%m-%d"), "time": mm_time.strftime("%H:%M:%S")}

# ---------------------- Record Live Data ----------------------
def record_live():
    """
    Called to save AM/Pm snapshots exactly at 12:01:00 and 16:30:00 Yangon time.
    If called at other times it still updates daily meta (date/time) but does not add Am/Pm.
    Returns result dict for logging/inspection.
    """
    now = datetime.datetime.now(pytz.timezone("Asia/Yangon"))
    string_date = now.strftime("%Y-%m-%d")
    string_time = now.strftime("%H:%M:%S")

    daily = load_daily()
    live_obj = get_live().get("live", {})
    # update daily metadata
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

        # Not exact save-times: update daily meta only (optional)
        save_daily(daily)
        print(f"[record_live] Updated daily meta for {string_date} at {string_time} (no AM/PM save)")
        return result
    except Exception as e:
        print(f"[record_live] Error while saving: {e}")
        result["error"] = str(e)
        return result

# ---------------------- Scheduler Setup (APScheduler) ----------------------
# Use Yangon timezone
yangon_tz = pytz.timezone("Asia/Yangon")

scheduler = BackgroundScheduler(timezone=yangon_tz)

# small wrapper to call record_live and print result (so background logs show activity)
def scheduled_record_wrapper(period_label):
    res = record_live()
    print(f"[scheduler:{period_label}] {res}")

# Add cron jobs: 12:01 and 16:30 Yangon time (seconds default to 0)
scheduler.add_job(lambda: scheduled_record_wrapper("AM"), 'cron', hour=12, minute=1, id="save_am", max_instances=1)
scheduler.add_job(lambda: scheduled_record_wrapper("PM"), 'cron', hour=16, minute=30, id="save_pm", max_instances=1)

# Ensure scheduler stops on exit
atexit.register(lambda: scheduler.shutdown(wait=False))

# ---------------------- API Routes ----------------------
@app.route("/api/all")
def api_all():
    live = get_live().get("live", {})
    daily = load_daily()
    history = load_history()
    server_time = string_date_time()
    response = {"live": live, "daily": daily, "history": history, "server_time": server_time}
    return jsonify(response)

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
    response = {"server_time": server_time, "live": live, "daily": daily, "history": history}
    return jsonify(response)

@app.route("/")
def root():
    live = get_live().get("live", {})
    server_time = string_date_time()
    daily = load_daily()
    history = load_history()
    return jsonify({"server_time": server_time, "live": live,"daily": daily, "history": history})

@app.route("/api/record", methods=["GET", "POST"])
def api_record():
    """
    Manual trigger to call record_live (useful for testing or if you want an external scheduler).
    """
    res = record_live()
    return jsonify(res)

# ---------------------- Run Server ----------------------
if __name__ == "__main__":
    # Start scheduler but avoid double-start when using Flask debug reloader
    # When debug=True, the reloader runs the script twice; WERKZEUG_RUN_MAIN is 'true' on the child process.
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        scheduler.start()
        print("[scheduler] Started (Asia/Yangon)")

    port = int(os.environ.get("PORT", 5000))
    # In development you can leave debug=True, but be aware of reloader behavior handled above.
    app.run(host="0.0.0.0", port=port, debug=True)
