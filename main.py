import requests
from fastapi import FastAPI
import time

app = FastAPI()

@app.get("/api/set")
def get_set_index():
    url = "https://www.set.or.th/api/set/index/SET"
    try:
        resp = requests.get(url)
        data = resp.json()

        return {
            "ok": True,
            "data": {
                "index": "SET",
                "last": data.get("last"),
                "value_million_baht": data.get("value"),
                "fetched_at": int(time.time())
            }
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

