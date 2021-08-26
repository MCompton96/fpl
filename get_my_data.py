import urllib3
import certifi
from urllib3 import request
import json
import requests
from setting import *

http = urllib3.PoolManager(
       cert_reqs='CERT_REQUIRED',
       ca_certs=certifi.where())

base_url = 'https://fantasy.premierleague.com/api/'
url = base_url + f'entry/{FPL_SETTINGS["userID"]}/history/'

r = http.request('GET', url)
data = json.loads(r.data.decode('utf-8'))

gw_data = data['current']

with open('data/my_gw_data.json', 'w', encoding='utf-8') as f:
    json.dump(gw_data, f, ensure_ascii=True, indent=2)

session = requests.session()
url = 'https://users.premierleague.com/accounts/login/'
payload = {
 'password': FPL_SETTINGS["password"],
 'login': FPL_SETTINGS["username"],
 'redirect_uri': 'https://fantasy.premierleague.com/a/login',
 'app': 'plfpl-web'
}
r = session.post(url, data=payload)

response = session.get(f'https://fantasy.premierleague.com/api/my-team/{FPL_SETTINGS["userId"]}')
r = response.json()
squad = r['picks']
with open('data/my_squad.json', 'w', encoding='utf-8') as f:
    json.dump(squad, f, ensure_ascii=True, indent=2)
    
transfers = r['transfers']
with open('data/transfers.json', 'w', encoding='utf-8') as f:
    json.dump(transfers, f, ensure_ascii=True, indent=2)

url = base_url + f'entry/{FPL_SETTINGS["userId"]}/'

r = http.request('GET', url)
data = json.loads(r.data.decode('utf-8'))

with open('data/my_team_info.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=True, indent=2)