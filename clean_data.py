import pandas as pd
import json
import os
import numpy as np

teams = json.loads(pd.read_csv('data/teams.csv').to_json(orient="records"))
players = json.loads(pd.read_csv('data/players.csv').to_json(orient="records"))
fixtures = json.loads(pd.read_csv('data/fixtures.csv').to_json(orient="records"))
events = json.loads(pd.read_csv('data/events.csv').to_json(orient="records"))
positions = json.loads(pd.read_csv('data/positions.csv').to_json(orient="records"))

players_df = pd.read_csv('data/players.csv')

def get_gw():
    gw = 0
    for event in events:
        if event['is_current'] == True:
            gw = event['id']
    return gw

headers = ['first_name', 'second_name', 'minutes', 'total_points', 'points_per_game', 'team', 'element_type', 'now_cost', 'status', 'id']
data = players_df[headers]
total_players = len(data)
clean_players = []
i = 0
for i in range(total_players):
    player = {}
    for header in headers:
        try:
            player[header] = data[header][i].item()
        except:
            player[header] = data[header][i]

    player_name = player['first_name'] + ' ' + player['second_name']
    player['full_name'] = player_name.lower()

    stats_headers = ['minutes', 'total_points', 'points_per_game', 'now_cost']
    player_season_stats = { "season": "21/22"}
    for header in stats_headers:
        player_season_stats[header] = player[header]
        del player[header]
    player['seasons'] = [player_season_stats]
    clean_players.append(player)


for player in clean_players:
    p_name = player['first_name'] + '_' + player['second_name']
    for season in player['seasons']:
        df = pd.read_csv(f'data/players/{p_name}/history.csv')
        headers = ['total_points', 'minutes']
        data = df[headers]
        player_gw_history = []
        for i in range(len(data)):
            if data['minutes'][i] >= 60:
                player_gw_history.append(data['total_points'][i].item() - 2)
            elif 0 < data['minutes'][i] < 60:
                player_gw_history.append(data['total_points'][i].item() - 1)
            else: 
                player_gw_history.append(data['total_points'][i].item())
        season['gw_history'] = player_gw_history
        
clean_players = [player for player in clean_players if player['seasons'][0]['points_per_game'] > 0]

with open('data/players_cleaned.json', 'w', encoding='utf-8') as f:
    json.dump(clean_players, f, ensure_ascii=True, indent=2)

max_fer_points = 0
avg_fer_points = 0
for team in teams:
    fer = []
    for fixture in fixtures:
        if fixture['team_a'] == team['id']:
            fer.append(1- 0.1 * fixture['team_a_difficulty'])
        elif fixture['team_h'] == team['id']:
            fer.append(1 - 0.1 * fixture['team_h_difficulty'])
        if len(fer) == 5:
            break
    team['fer'] = fer
    team['fer_points'] = np.mean(fer) * (1 - np.var(fer))
    avg_fer_points += team['fer_points']

avg_fer_points /= len(teams)
for team in teams:
    team['fer_points'] = round(team['fer_points'] / avg_fer_points, 3)
    if team['fer_points'] > max_fer_points:
        max_fer_points = team['fer_points']

sorted_teams = sorted(teams, key=lambda k: k['fer_points'], reverse=True)
with open('data/teams_cleaned.json', 'w', encoding='utf-8') as f:
    json.dump(sorted_teams, f, ensure_ascii=True, indent=2)

max_consistency = {
    '21/22': 0
}

with open('data/players_cleaned.json', 'r') as f:
    cleaned_players = json.load(f)

for player in cleaned_players:
    player['position'] = positions[player['element_type'] - 1]
    player['value_points'] = 0

    for team in teams:
        if team['id'] == player['team']:
            player['team_name'] = team['name']
            player['fer'] = team['fer_points']
            if team['fer_points'] >= 1:
                player['value_points'] += 10
            else:
                player['value_points'] += 8
            break


    total_career_games = 0
    for season in player['seasons']:
        season['effective_total_points'] = np.sum(season['gw_history']).item()
        season['gw_avg_points'] = np.mean(season['gw_history']).item()
        season['variance'] = np.var(season['gw_history']).item()
        season['consistency_factor'] = season['gw_avg_points'] * (100 - season['variance'])
        if season['consistency_factor'] > max_consistency[season['season']]:
            max_consistency[season['season']] = season['consistency_factor']
        del season['gw_history']
        if season['total_points'] != 0 and season['points_per_game'] != 0:
            season['total_games'] = round(season['total_points'] / season['points_per_game'])
        else:
            season['total_games'] = 0
        total_career_games += season['total_games']
        season['now_cost'] /= 10
        if season['total_games'] != 0 and total_career_games != 0:
            season['season_factor'] = ((season['total_games'] / total_career_games) + 1) / 2
        else:
            season['season_factor'] = 0



with open('data/players_cleaned.json', 'w', encoding='utf-8') as f:
    json.dump(cleaned_players, f, ensure_ascii=True, indent=2)

with open('data/players_cleaned.json', 'r') as f:
    players_cleaned = json.load(f)

    # normalize season consistency factor and award the value points
    for index, player in enumerate(players_cleaned):
        player['consistency_overall'] = 0
        for season in player['seasons']:
            if max_consistency[season['season']] != 0:
                season['consistency_factor'] /= max_consistency[season['season']]
            else:
                season['consistency_factor'] = 0
            player['consistency_overall'] += season['consistency_factor'] * season['season_factor']
            if season['consistency_factor'] >= 0.8:
                player['value_points'] += 8 * season['season_factor']
            elif 0.8 > season['consistency_factor'] >= 0.6:
                player['value_points'] += 7 * season['season_factor']
            elif 0.6 > season['consistency_factor'] >= 0.4:
                player['value_points'] += 6 * season['season_factor']
            elif 0.4 > season['consistency_factor'] >= 0.2:
                player['value_points'] += 5 * season['season_factor']
            elif 0.2 > season['consistency_factor'] >= 0:
                player['value_points'] += 4 * season['season_factor']
                
with open('data/players_cleaned.json', 'w', encoding='utf-8') as f:
    json.dump(players_cleaned, f, ensure_ascii=True, indent=2)

league_data = {
    'all_players_effective_total_points': 0,
    'all_players_minutes': 0,
    'total_players': 0
}

current_gameweek = get_gw()

with open('data/players_cleaned.json', 'r') as f:
    cleaned_players = json.load(f)

league_data['total_players'] = len(cleaned_players)

for player in cleaned_players:
    for season in player['seasons']:
        league_data['all_players_effective_total_points'] += season['effective_total_points']
        league_data['all_players_minutes'] += season['minutes']
        
league_data['avg_effective_total_points_per_player'] = league_data['all_players_effective_total_points'] / league_data['total_players']
league_data['avg_minutes_per_player'] = league_data['all_players_minutes'] / league_data['total_players']
league_data['avg_minutes_per_player'] /= current_gameweek

max_value_points = 0
for player in cleaned_players:
    for season in player['seasons']:
        minutes_per_game = season['minutes'] / season['total_games']
        if minutes_per_game >= 60:
            try:
                player['value_points'] += 4 * season['season_factor']
            except:
                print('Zero division error occurred')
        elif 60 > minutes_per_game >= league_data['avg_minutes_per_player']:
            try: 
                player['value_points'] += 3 * season['season_factor']
            except:
                print('Zero division error occurred')
        elif 0 < minutes_per_game < league_data['avg_minutes_per_player']:
            try: 
                player['value_points'] += 2 * season['season_factor']
            except:
                print('Zero division error occurred')
    if player['value_points'] > max_value_points:
        max_value_points = player['value_points']
        
            
for player in cleaned_players:
    player['fer'] /= max_fer_points
    player['value_points'] /= max_value_points
    
for player in cleaned_players:
    value = 0
    for season in player['seasons']:
        season['value'] = season['effective_total_points'] / league_data['avg_effective_total_points_per_player']
        value += season['value'] * season['season_factor']
    
    player['final_value'] = 53 * value + 27 * player['fer'] + 13.5 * player['consistency_overall'] + 9.5 * player['value_points']
    player['final_value_per_cost'] = player['final_value'] / player['seasons'][0]['now_cost']
    

with open('data/league_stats.json', 'w', encoding='utf-8') as f:
    json.dump(league_data, f, ensure_ascii=True, indent=2)

final_players_sorted = sorted(cleaned_players, key=lambda k: (-k['final_value']))

for player in final_players_sorted:
    player['position_name'] = player['position']['singular_name']

with open('data/final_players_sorted.json', 'w', encoding='utf-8') as f:
    json.dump(final_players_sorted, f, ensure_ascii=True, indent=2)
