from fastapi import FastAPI
import os, json, base64, time, requests
from datetime import datetime
import pytz
from bs4 import BeautifulSoup

from fastapi import FastAPI
def fetch_live_data():
    LINK_D = "THA_LIN"
    response = requests.get(LINK_D)
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find_all("table")[1]
    set_index = table.find_all("div")[4]
    value_index = table.find_all("div")[6]

    live_set = set_index.get_text(strip=True)
    live_value = value_index.get_text(strip=True)

    clean_set = live_set.replace(",", "")
    top = str(float(clean_set))[-1]

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

def save_to_github(new_data):
    token = os.getenv("TICKET_SC")
    repo = os.getenv("MY_T")
    path = "ResultsHistory.json"

    headers = {"Authorization": f"token {token}"}
    api_url = f"https://api.github.com/repos/{repo}/contents/{path}"

    r = requests.get(api_url, headers=headers)
    if r.status_code == 200:
        content = r.json()
        sha = content["sha"]
        old_data = json.loads(base64.b64decode(content["content"]).decode())
    else:
        sha = None
        old_data = []

    old_data.append(new_data)
    new_content = json.dumps(old_data, indent=4, ensure_ascii=False)

    commit_data = {
        "message": f"Update ResultsHistory.json at {new_data['time']}",
        "content": base64.b64encode(new_content.encode()).decode(),
        "sha": sha
    }
    r = requests.put(api_url, headers=headers, data=json.dumps(commit_data))

    if r.status_code in [200,201]:
        print("✅ Commit success")
    else:
        print("❌ Commit failed:", r.text)

if __name__ == "__main__":
    data = fetch_live_data()
    save_to_github(data)
