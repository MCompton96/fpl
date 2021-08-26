import urllib3
import certifi
from urllib3 import request
import json
import pandas as pd
import numpy as np
import os
import csv

http = urllib3.PoolManager(
       cert_reqs='CERT_REQUIRED',
       ca_certs=certifi.where())

base_url = 'https://fantasy.premierleague.com/api/'

def get_df(endpoint, json_key=None):
    url = base_url + endpoint
    r = http.request('GET', url)
    data = json.loads(r.data.decode('utf-8'))
    df = pd.json_normalize(data, json_key)
    return df

def get_player_data(player_id, json_key):
    endpoint = 'element-summary/' + str(player_id) + '/'
    df = get_df(endpoint, json_key)
    return df

main_endpoint = 'bootstrap-static/'
events_df = get_df(main_endpoint, 'events')
teams_df = get_df(main_endpoint, 'teams')
players_df = get_df(main_endpoint, 'elements')
positions_df = get_df(main_endpoint, 'element_types')
fixtures_df = get_df('fixtures/')

if not os.path.exists('data'):
    os.mkdir('data')

os.chdir('data')
events_df.to_csv('events.csv', index=False)
players_df.to_csv('players.csv', index=False)
teams_df.to_csv('teams.csv', index=False)
positions_df.to_csv('positions.csv', index=False)
fixtures_df.to_csv('fixtures.csv', index=False)

if not os.path.exists('players'):
    os.mkdir('players')

os.chdir('players')
for ind in players_df.index:
    full_name = players_df['first_name'][ind] + "_" + players_df['second_name'][ind]
    if not os.path.exists(f'{full_name}'):
        os.mkdir(f'{full_name}')
    
    os.chdir(f'{full_name}')
    
    player_id = players_df["id"][ind].astype(np.int32)
    
    player_history_df = get_player_data(player_id, 'history')
    player_prev_seasons_df = get_player_data(player_id, 'history_past')
    player_fixtures_df = get_player_data(player_id, 'fixtures')
    
    player_history_df.to_csv('history.csv', index=False)
    player_prev_seasons_df.to_csv('prev_seasons.csv', index=False)
    player_fixtures_df.to_csv('fixtures.csv', index=False)
    os.chdir('../')