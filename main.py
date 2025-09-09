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
    headers = {"User-Agent": "Mozilla/5.0"}  # prevent block
    resp = requests.get(url, headers=headers)

    soup = BeautifulSoup(resp.text, "html.parser")

    # Example: you may need to inspect HTML for exact selector
    # try to locate "SET Index" and "Value (M.Baht)" inside the page
    tables = soup.find_all("table")
    set_index = None
    value_mbaht = None

    if tables:
       
        table = tables[1]
        divs = table.find_all("div")
        try:
            set_index = divs[4].get_text(strip=True)
            value_mbaht = divs[6].get_text(strip=True)
        except:
            pass

    return {
        "ok": True,
        "data": {
            "set_index": set_index,
            "value_million_baht": value_mbaht,
            "fetched_at": int(time.time())
        }
    }


