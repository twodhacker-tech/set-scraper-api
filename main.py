from fastapi import FastAPI
from datetime import datetime
from pytz import timezone
import requests
from bs4 import BeautifulSoup
import time

app = FastAPI()

@app.get("/")
def twod():
    #1.Date and time
     mm_date = datetime.now(pytz.timezone("Asia/Yangon")).strftime("%Y-%m-%d ")
   mm_time = datetime.now(pytz.timezone("Asia/Yangon")).strftime("%H:%M:%S")
   #2.bs4 scraper 
    url = "https://www.set.or.th/en/market/product/stock/overview"   
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find_all("table")[1]
    set_index=table.find_all("div")[4]
    value_index=table.find_all("div")[6]
    Live_set=set_index.string
    Liver_value=value_index.string
    return {
            "date":mm_date,
            "time":mm_time,
        "Live": {
            "set": Live_set.strip(),
            "value": Liver_value.strip(),
            "fetched_at": int(time.time())
        }
    }