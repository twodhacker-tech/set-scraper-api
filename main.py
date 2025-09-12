from fastapi import FastAPI
from datetime import datetime
from pytz import timezone
import requests
from bs4 import BeautifulSoup
import time

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
    Live_value=value_index.string
    return {

        "Live": {
            "set": Live_set.strip(),
            "value": Live_value.strip(),
            "fetched_at": int(time.time())
        }
    }