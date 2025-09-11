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
    
    
  
        ResultsHistory=[]
        if os.path.exists("set_history.json"):
            with open("set_history.json","r",enxoding="utf-8") as f:
                history = json.load(f)
          return {
        
        "Live": {"date":now_mmt.strftime("%Y-%m-%d"),
                 "time":now_mmt.strftime("%H:%M:%S"),
            "live_set": Live_set.strip(),
            "live_value": Liver_value.strip(),
            "Results":history,
            "fetched_at": int(time.time())
                }
    }
