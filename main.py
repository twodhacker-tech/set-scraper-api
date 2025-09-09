from fastapi import FastAPI
import requests
from bs4 import BeautifulSoup
import time

app = FastAPI()

@app.get("/")
def home():
    url = "https://www.set.or.th/en/market/product/stock/overview"   
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find_all("table")[1]
    set_index=table.find_all("div")[4]
    value_index=table.find_all("div")[6]
    Live_set=set_index.string
    Liver_value=value_index.string
    return {
        
        "Live": {
            "set_index": Live_set.strip(),
            "value_index": Liver_value.strip(),
            "fetched_at": int(time.time())
        }
    }
