import json
import datetime
import pytz
import os
import time
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify

app = Flask(name)

DATA_FILE = "ResultsHistory.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            file_content = f.read()  # ဖိုင်ကိုဖတ်ပြီး data ကြည့်ပါ
            print(file_content)  # ဖိုင်အကြောင်းကို debug ရန် print ထုတ်ပါ
            data = json.loads(file_content)

            # Check if 'record' is null, remove it from data
            if data.get("record") is None:
                del data["record"]

            return data
    except Exception as e:
        print(f"Error: {e}")  # အမှားတစ်ခုရှိရင် ဖော်ပြပါ
        return {
            "date": "--",
            "time": "--",
            "live": {},
            "12:01:00": {},
            "4:30:00": {}
        }
def save_data(data):
    # Delete 'record' key before saving the data, if it's there
    if "record" in data:
        del data["record"]  # record key ကို remove လုပ်ပါ

    # Open file to save data
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)  # This line should be indented
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
if clean_value in ["", "-"]:   # ဒေတာမရှိရင်  
    clean_value = "0.00"  
last = str(int(float(clean_value)))[-1]  

twod_live = f"{top}{last}"  
return {
    "live": {"twod": twod_live,"set": live_set,"value": live_value,"fetched_at": int(time.time())}  
        }

def string_date_time():
mm_time = datetime.datetime.now(pytz.timezone("Asia/Yangon"))
string_date= mm_time.strftime("%Y-%m-%d")
string_time= mm_time.strftime("%H:%M:%S")
return{
    "date": string_date,"time": string_time
}

def record_live():
    # Get current time in Yangon timezone (seconds ပါအောင်)
    now = datetime.datetime.now(pytz.timezone("Asia/Yangon")).strftime("%H:%M:%S")

    # Load data and get live data  
    data = load_data()  
    live = get_live()  

    # Check for AM / PM times
    if now == "12:01:00":  
        data["Am"] = live["live"]  
        save_data(data)  # 12:01 မှာ save လုပ်ထား

    if now == "16:30:00":  
        data["Pm"] = live["live"]  
        save_data(data)  # 16:30 မှာ save လုပ်ထား

        return live["live"]  # 16:30 မှာ live data ကို return ပြန်

    return data  # မဟုတ်ရင် data ကို return ပြန်

@app.route("/api/data")
def api_data():
return jsonify(record_live())

@app.route("/")
def root():
return jsonify({
    **string_date_time(),
    **get_live(),
    **record_live()
})

if name == "main":
port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port, debug=True)

