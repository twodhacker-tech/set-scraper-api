import json
import datetime
import pytz
import os
import time
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify

app = Flask(__name__)

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


