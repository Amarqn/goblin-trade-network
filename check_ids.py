import requests
from config import *

token = requests.post('https://oauth.battle.net/token', data={'grant_type':'client_credentials'}, auth=(BLIZZARD_CLIENT_ID, BLIZZARD_CLIENT_SECRET)).json()['access_token']

top_ids = [82800, 239675, 239672, 244591, 240959, 237924, 237952, 244626, 244596, 240947]

for item_id in top_ids:
    r = requests.get(f'https://eu.api.blizzard.com/data/wow/item/{item_id}', headers={'Authorization': f'Bearer {token}'}, params={'namespace': 'static-eu', 'locale': 'fr_FR'})
    if r.status_code == 200:
        name = r.json().get('name', 'Inconnu')
        print(f"  {item_id}: {name}")
    else:
        print(f"  {item_id}: Erreur {r.status_code}")