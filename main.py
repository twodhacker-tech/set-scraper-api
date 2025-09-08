from fastapi import FastAPI, HTTPException
import httpx
from bs4 import BeautifulSoup
import time
import re

app = FastAPI(title="SET Scraping API", version="0.1.0")

CACHE = {}
CACHE_TTL = 30  # seconds
SET_URL = "https://www.set.or.th/en/home"

def fetch_set_index():
    now = time.time()
    cached = CACHE.get("set_index")
    if cached and now - cached["ts"] < CACHE_TTL:
        return cached["data"]

    try:
        resp = httpx.get(SET_URL, timeout=15.0)
        resp.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Fetch failed: {str(e)}")

    soup = BeautifulSoup(resp.text, "html.parser")

    row = None
    for el in soup.find_all(text=re.compile(r"SET Index")):
        row = el.parent.get_text(" ", strip=True)
        break

    if not row:
        raise HTTPException(status_code=500, detail="Could not parse SET index")

    nums = re.findall(r"\d{1,3}(?:,\d{3})*(?:\.\d+)?", row)

    data = {
        "index_name": "SET Index",
        "numbers": nums,
        "raw_text": row,
        "fetched_at": int(now),
    }

    CACHE["set_index"] = {"ts": now, "data": data}
    return data

@app.get("/api/set")
def get_set_index():
    return {"ok": True, "data": fetch_set_index()}

@app.get("/")
def root():
    return {
        "message": "Welcome to Thai SET Scraping API",
        "endpoints": ["/api/set"],
    }
