import requests
from bs4 import BeautifulSoup

url = "https://www.set.or.th/en/market/product/stock/overview"   
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")
table = soup.find_all("table")[1]
set=table.find_all("div")[4]
value=table.find_all("div")[6]
print(set.string)
print(value.string)