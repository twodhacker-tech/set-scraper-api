from fastapi import FastAPI
from flask import flask, jsonify
from datetime import datetime
from pytz import timezone
import requests
from bs4 import BeautifulSoup
from datetime import datetime



app = FastAPI()

@app.get("/")
def twod():
    url = "https://www.set.or.th/en/market/product/stock/overview"   
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find_all("table")[1]
    set_index=table.find_all("div")[4]
    value_index=table.find_all("div")[6]
    Live_set=set_index.string
    Liver_value=value_index.string

def mm_datetime():
    # Myanmar Timezone
    mm_time = datetime.now(pytz.timezone("Asia/Yangon"))
    "mm_date"=mm_time.strftime("%Y-%m-%d )
    "mm_time"=mm_time.strftime(%H:%M:%S")

    return {
            "date":mm_date,
            "time":mm_time,
        "Live": {
            "set": Live_set.strip(),
            "value": Liver_value.strip(),
            "fetched_at": int(time.time())
        }
    }