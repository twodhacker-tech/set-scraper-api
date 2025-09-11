from fastapi import FastAPI
from datetime import datetime
from pytz import timezone
import requests,json,os
from bs4 import BeautifulSoup

app = FastAPI()
MMT = timezone("Asia,Yangon")

@app.get("/")
def history_data():
        if os.path.exists("ResultsHistory.json"):
            with open("ResultHistory.json","r",enxoding="utf-8") as f:
                history = json.load(f)
def Twod_Live():
    url = "https://www.set.or.th/en/market/product/stock/overview"   
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find_all("table")[1]
    set_index=table.find_all("div")[4]
    value_index=table.find_all("div")[6]
    Live_set=set_index.string
    Liver_value=value_index.string
    now_mmt = datetime.now(MMT)
    live= Twod_Live()

         return {
                 "date":now_mmt.strftime("%d-%m-%Y"),
                 "time":now_mmt.strftime("%H:%M:%S"),
              "live": {
            "set": Live_set.strip(),
            "value": Live_value.strip()},
              "History": [{"am":"12:01","set":"--","value":"--"},{"pm":"4:30","set":"--","value":"--"}]
            "fetched_at": int(time.time())
                  }
