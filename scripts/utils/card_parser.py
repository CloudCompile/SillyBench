import json
import os

def parse_card(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle V3 structure where data is nested in 'data' or top-level V2
    card_data = data.get('data', data)
    
    name = card_data.get('name', 'Unknown')
    description = card_data.get('description', '')
    personality = card_data.get('personality', '')
    scenario = card_data.get('scenario', '')
    first_mes = card_data.get('first_mes', '')
    mes_example = card_data.get('mes_example', '')
    alternate_greetings = card_data.get('alternate_greetings', [])

    return {
        'name': name,
        'description': description,
        'personality': personality,
        'scenario': scenario,
        'first_mes': first_mes,
        'mes_example': mes_example,
        'alternate_greetings': alternate_greetings
    }
