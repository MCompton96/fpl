import numpy as np
import pandas as pd
import json
from random import shuffle

events = json.loads(pd.read_csv('data/events.csv').to_json(orient="records"))
with open('data/my_gw_data.json', 'r') as f:
    gw_history = json.load(f)
with open('data/my_squad.json', 'r') as f:
    my_squad = json.load(f)
    
with open('data/my_team_info.json', 'r') as f:
    team_info = json.load(f)
current_gameweek = 0
for event in events:
    if event['is_current'] == True:
        current_gameweek = event['id']

with open('data/final_players_sorted.json', 'r') as f:
    players = json.load(f)

with open('data/transfers.json', 'r') as f:
    transfer_info = json.load(f)
    
with open('data/teams_cleaned.json', 'r') as f:
    teams = json.load(f)
    
limit = {
    'cost_limit': np.var([player['seasons'][0]['now_cost'] for player in players]),
    'consistency_limit': np.var([player['consistency_overall'] for player in players]) * 100, 
    'final_value_limit': np.var([player['final_value'] for player in players]) / 1000,
    'value_points_limit': np.var([player['value_points'] for player in players]) * 100, 
    'variance_points_limit': np.var([player['fer'] for player in players]) * 100,
}


gw_transfers_left = transfer_info['limit'] - transfer_info['made']
gw_money_available = transfer_info['bank'] / 10

team_players_selected = {}
for team in teams:
    team_players_selected[team["name"]] = 0

def get_configuration():
    return {
        'Goalkeeper': {
            'left': 2
        },
        'Defender': {
            'left': 5
        },
        'Midfielder': {
            'left': 5
        },
        'Forward': {
            'left': 3
        }
    }

def get_formations():
    
    return [
        {
            'Goalkeeper': 1,
            'Defender': 3,
            'Midfielder': 5,
            'Forward': 1
        },
        {
            'Goalkeeper': 1,
            'Defender': 3,
            'Midfielder': 4,
            'Forward': 3
        },
        {
            'Goalkeeper': 1, 
            'Defender': 4, 
            'Midfielder': 3,
            'Forward': 3
        },
        {
            'Goalkeeper': 1, 
            'Defender': 4, 
            'Midfielder': 4,
            'Forward': 2
        },
        {
            'Goalkeeper': 1, 
            'Defender': 4, 
            'Midfielder': 5,
            'Forward': 1
        },
        {
            'Goalkeeper': 1, 
            'Defender': 5, 
            'Midfielder': 3,
            'Forward': 2
        },
        {
            'Goalkeeper': 1, 
            'Defender': 5, 
            'Midfielder': 4,
            'Forward': 1
        }
    ]

def get_positions():
    
    return {
        1: 'Goalkeeper',
        2: 'Defender',
        3: 'Midfielder',
        4: 'Forward'
    }

def get_budget():
    
    return team_info['last_deadline_value'] / 10

def get_my_players():
    my_players = []
    for squad_player in my_squad:
        for player in players:
            if squad_player['element'] == player['id']:
                my_players.append(player)
    
    return my_players

def get_not_interested():
    return []

goalkeepers = [player for player in players if player['position_name'] == 'Goalkeeper']
defenders = [player for player in players if player['position_name'] == 'Defender']
midfielders = [player for player in players if player['position_name'] == 'Midfielder']
forwards = [player for player in players if player['position_name'] == 'Forward']

def get_team_cost(team):
    cost = 0
    for player in team:
        cost += player['seasons'][0]['now_cost']
    
    return round(cost, 2)


def get_player_cost(player_name):
    for player in players:
        if player['full_name'] == player_name:
            return player['seasons'][0]['now_cost']
    return 0
    
def get_formation(team):
    formation = [0, 0, 0]
    for player in team:
        if player['position_name'] == 'Defender':
            formation[0] += 1
        elif player['position_name'] == 'Midfielder':
            formation[1] += 1
        elif player['position_name'] == 'Forward':
            formation[2] += 1
    
    formation = [str(x) for x in formation]
    return '-'.join(formation)

def get_estimated_points(team):
    points = 0
    for player in team:
        points += player['seasons'][0]['total_points']
    
    return team_info['summary_overall_points'] + round(points * (38 - current_gameweek))

def value_in_range(player1, player2):
    a = max(player1['final_value'], player2['final_value'])
    b = min(player1['final_value'], player2['final_value'])
    
    ans = (a - b) * 100 / a
    
    if ans <= limit['final_value_limit']:
        return [True, player1 if a == player1['final_value'] else player2]
    else:
        return [True, player1 if a == player1['final_value'] else player2]
    
def budget_in_range(amount1, amount2):
    
    if amount2 < 0:
        return False
    elif amount2 < amount1:
        a = max(amount1, amount2)
        b = min(amount1, amount2)
        ans = (a - b) * 100 / a
        if ans <= limit['cost_limit']:
            return True
        else:
            return False
    elif amount2 > amount1:
        return True
    
def value_points_in_range(player1, player2):
    a = max(player1['value_points'], player2['value_points'])
    b = min(player1['value_points'], player2['value_points'])
    
    ans = (a - b) * 100 / a
    
    if ans <= limit['value_points_limit']:
        return [True, player1 if a == player1['value_points'] else player2]
    else:
        return [False, player1 if a == player1['value_points'] else player2]

def consistency_in_range(player1, player2):
    a = max(player1['consistency_overall'], player2['consistency_overall'])
    b = min(player1['consistency_overall'], player2['consistency_overall'])
    
    ans = (a - b) * 100 / a
    
    if ans <= limit['consistency_limit']:
        return [True, player1 if a == player1['consistency_overall'] else player2]
    else:
        return [False, player1 if a == player1['consistency_overall'] else player2]
    
def player_with_easy_fixtures(player1, player2):
    if player1['fer'] >= player2['fer']:
        return player1
    else:
        return player2

def get_cover(player_type, final_team, configuration, new_player=''):
    
    forward_cost = np.mean([player['seasons'][0]['now_cost'] for player in players if player['position_name'] == 'Forward' and player not in final_team])
    midfielder_cost = np.mean([player['seasons'][0]['now_cost'] for player in players if player['position_name'] == 'Midfielder' and player not in final_team])
    defender_cost = np.mean([player['seasons'][0]['now_cost'] for player in players if player['position_name'] == 'Defender' and player not in final_team])
    goalkeeper_cost = np.mean([player['seasons'][0]['now_cost'] for player in players if player['position_name'] == 'Goalkeeper' and player not in final_team])

    cover = 0
    for position in configuration:
        if position == 'Goalkeeper':
            cover += configuration[position]['left'] * goalkeeper_cost
        elif position == 'Defender':
            cover += configuration[position]['left'] * defender_cost
        elif position == 'Midfielder':
            cover += configuration[position]['left'] * midfielder_cost
        elif position == 'Forward':
            cover += configuration[position]['left'] * forward_cost
    
    if player_type == 'Goalkeeper':
        cover -= goalkeeper_cost
    elif player_type == 'Defender':
        cover -= defender_cost
    elif player_type == 'Midfielder':
        cover -= midfielder_cost
    elif player_type == 'Forward':
        cover -= forward_cost
    return cover

def select_player_from(position, final_team, configuration, budget, team_players_selected, donot_consider, picks=0):
    
    if position == 'Goalkeeper':
        global goalkeepers
        position = goalkeepers
    if position == 'Defender':
        global defenders
        position = defenders
    if position == 'Midfielder':
        global midfielders
        position = midfielders
    if position == 'Forward':
        global forwards
        position = forwards

    
    for _ in range(picks):
        
        selected_players = []
        budget = get_budget()
        
        i = 0
        while len(selected_players) < 2 and i < len(position):
            cover = get_cover(position[0]['position_name'], final_team, configuration)
            b = budget - position[i]['seasons'][0]['now_cost']
            
            if budget_in_range(cover, budget - position[i]['seasons'][0]['now_cost']):
                if position[i] not in final_team and budget > position[i]['seasons'][0]['now_cost'] and configuration[position[i]['position_name']]['left'] > 0 and team_players_selected[position[i]['team_name']] < 3 and position[i]['status'] == 'a' and position[i] not in donot_consider and position[i] not in selected_players:
                    selected_players.append(position[i])
            else:
                donot_consider.append(position[i])
            
            i += 1
        
        if len(selected_players) == 1:
            return selected_players[0]
        
        elif len(selected_players) == 0:
            position = sorted(position, key=lambda k: (k['seasons'][0]['now_cost'], -k['final_value']))
            
            i = 0
            while position[i] in final_team:
                i += 1
            
            if len(selected_players) <= i + 1 and len(selected_players) > 0:
                return selected_players[i]
            
        else:
            if value_in_range(selected_players[0], selected_players[1])[0]:
                if value_points_in_range(selected_players[0], selected_players[1]):
                    if consistency_in_range(selected_players[0], selected_players[1]):
                        return player_with_easy_fixtures(selected_players[0], selected_players[1])
                    else:
                        return consistency_in_range(selected_players[0], selected_players[1])[1]
                    
                else:
                    return value_points_in_range(selected_players[0], selected_players[1])[1]
            
            else:
                return value_in_range(selected_players[0], selected_players[1])[1]


def get_best_playing_11_points(final_team):
    final_team = sorted(final_team, key=lambda k: k['final_value'], reverse=True)
    
    formations = get_formations()
    max_points = 0
    
    for formation in formations:
        playing_team = []
        for player in final_team:
            
            if formation[player['position_name']] > 0:
                playing_team.append(player)
                formation[player['position_name']] -= 1
        
        points = get_estimated_points(playing_team)
        
        if points > max_points:
            max_points = points
            
    return max_points


def create_team(omit_player=None, iterations=1000):
    
    positions = ['Forward']*3 + ['Midfielder']*5 + ['Defender']*5 + ['Goalkeeper']*2
    my_players = get_my_players()
    
    for player in players:
        if player['full_name'] in my_players and player['full_name'] != omit_player and player['position_name'] in positions:
            positions.remove(player['position_name'])
    
    best_team = []
    max_points = -1
    
    for x in range(iterations):
        
        configuration = get_configuration()
        final_team = []
        donot_consider = []
        budget = get_budget()
        
        for player in players:
            if player['full_name'] in my_players and player['full_name'] != omit_player:
                budget -= player['seasons'][0]['now_cost']
                configuration[player['position_name']]['left'] -= 1
                team_players_selected[player['team_name']] += 1
                final_team.append(player)
        
        not_interested = get_not_interested()
        for player in players:
            if player['full_name'] in not_interested:
                donot_consider.append(player)
        
        shuffle(positions)
        
        for p in positions:
            player = select_player_from(p, final_team, configuration, budget, team_players_selected, donot_consider, 1)
            if player is not None:
                budget -= player['seasons'][0]['now_cost']
                configuration[player['position_name']]['left'] -= 1
                team_players_selected[player['team_name']] += 1
                final_team.append(player)
                
        points = get_best_playing_11_points(final_team)
        
        if points > max_points:
            max_points = points
            best_team = final_team
            
    return (best_team, max_points)

def get_transfers():
    
    current_team_expected_points = create_team(iterations=1)[1]
    max_points = -1
    best_transfers = []
    my_players = get_my_players()
    
    for y in range(len(my_players) - 1):
        omit_player = my_players[y]
        best_team, points = create_team(omit_player, iterations=1)
        
        if points > max_points:
            max_points = points
        
        for player in best_team:
            if player['full_name'] not in my_players:
                best_transfers.append(
                {
                    'out': {
                        'name': omit_player['full_name'],
                        'cost': get_player_cost(omit_player['full_name']),
                    },
                    'in': {
                        'name': player['full_name'],
                        'cost': get_player_cost(player['full_name'])
                    },
                    'points': points,
                    'g/l': points - current_team_expected_points
                }
                )
                break
        
        best_transfers = sorted(best_transfers, key=lambda k: (-k['points']))
        
        return best_transfers

transfers = get_transfers()

with open('data/my_transfers.json', 'w', encoding='utf-8') as f:
    json.dump(transfers, f, ensure_ascii=True, indent=2)


