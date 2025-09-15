from flask import Flask, jsonify
import json
import datetime
import pytz
import os
import requests   # API ကနေ data ယူဖို့

app = Flask(__name__)

DATA_FILE = "ResultsHistory.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {
 "date": mm_time.strftime("%Y-%m-%d"),
        "time": mm_time.strftime("%H:%M:%S"),
        "hour": mm_time.strftime("%H"),
        "minutes": mm_time.strftime("%M"),
        "second": mm_time.strftime("%S"),
        "live": {
            "twod": twod_live,
            "set": live_set,
            "value": live_value,
            "fetched_at": int(time.time())
        },
  "results": {"12:01":{
            "twod": --,
            "set": --,
            "value": --
        },
             "4:30":{
            "twod": --,
            "set": --,
            "value": --
        }
}
}

def save_data(data):
    with open(DATA_FILE, "w") as f:
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

    clean_set = live_set.replace(",", "")
    formatted="{:.2f}".format(float(clean_set))
    top = formatted[-1]

    clean_value = live_value.replace(",", "")
    last = str(int(float(clean_value)))[-1]

    twod_live = f"{top}{last}"

    mm_time = datetime.now(pytz.timezone("Asia/Yangon"))
    return {
        "date": mm_time.strftime("%Y-%m-%d"),
        "time": mm_time.strftime("%H:%M:%S"),
        "hour": mm_time.strftime("%H"),
        "minutes": mm_time.strftime("%M"),
        "second": mm_time.strftime("%S"),
        "live": {
            "twod": twod_live,
            "set": live_set,
            "value": live_value,
            "fetched_at": int(time.time())
        }
    }

def record_live():
    yangon = pytz.timezone("Asia/Yangon")
    now = datetime.datetime.now(yangon).strftime("%H:%M")

    data = load_data()
    live = get_live()

    record_times = ["12:01", "16:30"]

    if now in record_times:
        data["results"][now] = live  # တိကျတဲ့အချိန် record

    data["current"] = live
    save_data(data)
    return data

@app.route("/api/data", methods=["GET"])
def api_data():
    data = record_live()
    return jsonify(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)