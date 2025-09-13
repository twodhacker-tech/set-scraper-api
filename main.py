from fastapi import FastAPI
from datetime import datetime
import pytz
import time
import requests
from bs4 import BeautifulSoup
import math

app = FastAPI()

@app.get("/")
def twod():
    url = "https://www.set.or.th/en/market/product/stock/overview"   
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Table data
    table = soup.find_all("table")[1]
    set_index = table.find_all("div")[4]
    value_index = table.find_all("div")[6]

    live_set = set_index.get_text(strip=True)
    live_value = value_index.get_text(strip=True)

   clean_set = live_set.replace(",", "")
extract_set = float(clean_set)
top = str(int(extract_set))[-1]  

clean_value = live_value.replace(",", "")
extract_value = float(clean_value)
last = str(int(extract_value))[-1] 

twod_live = int(f"{top}{last}")

    

# Myanmar Timezone
    mm_time = datetime.now(pytz.timezone("Asia/Yangon"))
    mm_date = mm_time.strftime("%Y-%m-%d")
    mm_time_str = mm_time.strftime("%H:%M:%S")

    return {
        "date": mm_date,
        "time": mm_time_str,
        "Live": {
            "live_twod":twod_live,
            "set": live_set,
            "value": live_value,
            "fetched_at": int(time.time())
        }
    }