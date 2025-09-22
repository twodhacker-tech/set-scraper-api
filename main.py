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
from apscheduler.schedulers.base import SchedulerAlreadyRunningError

app = Flask(__name__)

# ---------------------- File Names ----------------------
DATA_FILE_DAILY = os.path.join(os.path.dirname(__file__), "DailyResult.json")
DATA_FILE_HISTORY = os.path.join(os.path.dirname(__file__), "HistoryResult.json")

# ---------------------- Helpers: load/save ----------------------
def load_daily():
    try:
        with open(DATA_FILE_DAILY, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"[load_daily] Error: {e}")
        return {"date": "--", "time": "--", "Am": {}, "Pm": {}}

def save_daily(data):
    try:
        with open(DATA_FILE_DAILY, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[save_daily] Error: {e}")

def load_history():
    try:
        with open(DATA_FILE_HISTORY, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"[load_history] Error: {e}")
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
        print(f"[save_history] Error: {e}")

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
        table = tables[1]
        divs = table.find_all("div")
        live_set = divs[4].get_text(strip=True)
        live_value = divs[6].get_text(strip=True)

        clean_set = live_set.replace(",", "")
        formatted = "{:.2f}".format(float(clean_set))
        top = formatted[-1]

        clean_value = live_value.replace(",", "") or "0.00"
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
            return result

        if string_time == "18:05:00":
            daily["Pm"] = live_obj
            save_daily(daily)
            save_history(string_date, "Pm", live_obj)
            result.update({"saved": True, "period": "Pm"})
            return result

        save_daily(daily)
        return result
    except Exception as e:
        result["error"] = str(e)
        return result

# ---------------------- Scheduler Setup ----------------------
yangon_tz = pytz.timezone("Asia/Yangon")
scheduler = BackgroundScheduler(timezone=yangon_tz)

def scheduled_record_wrapper(period_label):
    res = record_live()
    print(f"[scheduler:{period_label}] {res}")

scheduler.add_job(lambda: scheduled_record_wrapper("AM"), 'cron', hour=12, minute=1, id="save_am", max_instances=1)
scheduler.add_job(lambda: scheduled_record_wrapper("PM"), 'cron', hour=16, minute=30, id="save_pm", max_instances=1)

atexit.register(lambda: scheduler.shutdown(wait=False))

# ---------------------- API Routes ----------------------
@app.route("/api/all")
def api_all():
    return jsonify({
        "live": get_live().get("live", {}),
        "daily": load_daily(),
        "history": load_history(),
        "server_time": string_date_time()
    })

@app.route("/api/daily")
def api_daily():
    return jsonify({"daily": load_daily()})

@app.route("/api/history")
def api_history():
    return jsonify({"history": load_history()})

@app.route("/api/record", methods=["GET", "POST"])
def api_record():
    return jsonify(record_live())

@app.route("/")
def root():
    return jsonify({
        "server_time": string_date_time(),
        "live": get_live().get("live", {}),
        "daily": load_daily(),
        "history": load_history()
    })

# ---------------------- Run Server ----------------------
if __name__ == "__main__":
    # avoid double start in debug reloader
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        try:
            scheduler.start()
            print("[scheduler] Started (Asia/Yangon)")
        except SchedulerAlreadyRunningError:
            print("[scheduler] Already running")

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)