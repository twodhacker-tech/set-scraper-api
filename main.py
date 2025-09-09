from fastapi import FastAPI
import requests
from bs4 import BeautifulSoup
import time

app = FastAPI()

@app.get("/")
def home():
    return {
        "Hackingtwod": "Hacking TwoD"
    }

@app.get("/api/set")
def get_set_index():
    url = "https://www.set.or.th/en/market/product/stock/overview"   
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find_all("table")[1]
    set_index=table.find_all("div")[4]
    value_index=table.find_all("div")[6]
    Live_set="SET:",set_index.string
    Liver_value="Value:",value_index.string
    return {
        "ok": True,
        "Live": {
            "set_index": Live_set,
            "value_index": Liver_value,
            "fetched_at": int(time.time())
        }
    }
