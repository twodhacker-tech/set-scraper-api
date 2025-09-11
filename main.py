from fastapi import FastAPI
from datetime import datetime
from pytz import timezone
import requests,json,os
from bs4 import BeautifulSoup

app = FastAPI()
MMT = timezone("Asia,Yangon")

@app.get("/")
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
    
    
 @app.get("/")
def history_data():
    live = Twod_Live()
    history = []
        if os.path.exists("ResultsHistory.json"):
            with open("ResultHistory.json","r",enxoding="utf-8") as f:
                history = json.load(f)
          return {
              "live": live,
              "history": history     
      
    }
