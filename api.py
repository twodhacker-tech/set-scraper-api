from fastapi import FastAPI
from datetime import datetime
import pytz, time, requests
from bs4 import BeautifulSoup

app = FastAPI()
def fetch_live_data():
    LINK_D = "THA_LIN"
    response = requests.get(LINK_D)
    TWODHACKER

@app.get("/")
def home():
    return fetch_live_data()
