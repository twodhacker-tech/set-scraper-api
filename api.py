from fastapi import FastAPI
from datetime import datetime
import pytz, time, requests
from bs4 import BeautifulSoup

app = FastAPI()
def fetch_live_data():
    url = "https://www.set.or.th/en/market/product/stock/overview"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find_all("table")[1]
    set_index = table.find_all("div")[4]
    value_index = table.find_all("div")[6]

    live_set = set_index.get_text(strip=True)
    live_value = value_index.get_text(strip=True)

    clean_set = live_set.replace(",", "")
    top = str(clean_set)[-1]

    clean_value = live_value.replace(",", "")
    last = str(int(float(clean_value)))[-1]

    twod_live = str(int(f"{top}{last}"))

    mm_time = datetime.now(pytz.timezone("Asia/Yangon"))
    return {
        "date": mm_time.strftime("%Y-%m-%d"),
        "time": mm_time.strftime("%H:%M:%S"),
        "Live": {
            "twod": twod_live,
            "set": live_set,
            "value": live_value,
            "fetched_at": int(time.time())
        }
    }

@app.get("/")
def home():
    return fetch_live_data()
