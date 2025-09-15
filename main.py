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

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)

    yangon = pytz.timezone("Asia/Yangon")
    mm_time = datetime.datetime.now(yangon)

    return {
        "date": mm_time.strftime("%Y-%m-%d"),
        "time": mm_time.strftime("%H:%M:%S"),
        "hour": mm_time.strftime("%H"),
        "minutes": mm_time.strftime("%M"),
        "second": mm_time.strftime("%S"),
        "live": {"twod":"--","set":"--","value":"--","fetched_at":0},
        "results": {
            "12:01":{"twod":"--","set":"--","value":"--"},
            "16:30":{"twod":"--","set":"--","value":"--"}
        }
    }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_live():
    url = "https://www.set.or.th/en/market/product/stock/overview"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find_all("table")[1]
    set_index = table.find_all("div")[4]
    value_index = table.find_all("div")[6]

    live_set = set_index.get_text(strip=True)
    live_value = value_index.get_text(strip=True)

    top = "{:.2f}".format(float(live_set.replace(",","")))[-1]
    last = str(int(float(live_value.replace(",",""))))[-1]
    twod_live = f"{top}{last}"

    mm_time = datetime.datetime.now(pytz.timezone("Asia/Yangon"))
    return {
        "date": mm_time.strftime("%Y-%m-%d"),
        "time": mm_time.strftime("%H:%M:%S"),
        "live": {
            "twod": twod_live,
            "set": live_set,
            "value": live_value,
            "fetched_at": int(time.time())
        }
    }

def record_live():
    now = datetime.datetime.now(pytz.timezone("Asia/Yangon")).strftime("%H:%M")
    data = load_data()
    live = get_live()
    for t in ["12:01","16:30"]:
        if now == t:
            data["results"][t] = live["live"]
    data["live"] = live["live"]
    save_data(data)
    return data

@app.route("/api/data")
def api_data():
    return jsonify(record_live())

@app.route("/")
def root():
    return jsonify(get_live(),record_live())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
