import json
import os
import datetime
import pytz
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from threading import Lock

app = Flask(__name__)

# ===== File Paths =====
BASE_DIR = os.path.dirname(__file__)
DATA_FILE_DAILY = os.path.join(BASE_DIR, "DailyResult.json")
DATA_FILE_HISTORY = os.path.join(BASE_DIR, "HistoryResult.json")

file_lock = Lock()

# ===== Helper Functions =====
def load_json(path):
    try:
        with file_lock:
            if not os.path.exists(path):
                return {}
            with open(path, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return {}

def save_json(path, data):
    try:
        with file_lock:
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving {path}: {e}")

def get_myanmar_time():
    tz = pytz.timezone("Asia/Yangon")
    now = datetime.datetime.now(tz)
    return now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")

# ===== Scraper Function =====
def fetch_live():
    tz = pytz.timezone("Asia/Yangon")
    now = datetime.datetime.now(tz)
    # TODO: Real scraping logic here
    live_data = {
        "fetched_at": int(now.timestamp()),
        "set": "1,297.21",
        "twod": str(now.second % 100).zfill(2),
        "value": "29,497.68"
    }
    return live_data

# ===== Save Functions =====
def save_daily_record():
    today, current_time = get_myanmar_time()
    data = load_json(DATA_FILE_DAILY)
    data[today] = {
        "date": today,
        "time": current_time,
        "live": fetch_live()
    }
    save_json(DATA_FILE_DAILY, data)
    print(f"[Daily] Saved at {current_time}")

def save_history_record():
    today, current_time = get_myanmar_time()
    data = load_json(DATA_FILE_HISTORY)
    if today not in data:
        data[today] = []
    data[today].append({
        "date": today,
        "time": current_time,
        "live": fetch_live()
    })
    save_json(DATA_FILE_HISTORY, data)
    print(f"[History] Saved at {current_time}")

# ===== Scheduler Setup =====
scheduler = BackgroundScheduler()

# 12:01 MMT
scheduler.add_job(save_daily_record, "cron", hour=12, minute=1, timezone="Asia/Yangon")
scheduler.add_job(save_history_record, "cron", hour=12, minute=1, timezone="Asia/Yangon")

# 16:30 MMT
scheduler.add_job(save_daily_record, "cron", hour=16, minute=30, timezone="Asia/Yangon")
scheduler.add_job(save_history_record, "cron", hour=16, minute=30, timezone="Asia/Yangon")

# ===== API Endpoints =====
@app.route("/live")
def api_live():
    return jsonify(fetch_live())

@app.route("/daily")
def api_daily():
    return jsonify(load_json(DATA_FILE_DAILY))

@app.route("/history")
def api_history():
    return jsonify(load_json(DATA_FILE_HISTORY))

@app.route("/")
def api_root():
    today, current_time = get_myanmar_time()
    return jsonify({
        "date": today,
        "time": current_time,
        "live": fetch_live(),
        "daily": load_json(DATA_FILE_DAILY),
        "history": load_json(DATA_FILE_HISTORY)
    })

# ===== Run App =====
if __name__ == "__main__":
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        scheduler.start()
        print("[scheduler] Started (Asia/Yangon)")

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)