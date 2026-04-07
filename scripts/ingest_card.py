import os
import json
import uuid
import sys
from utils.card_parser import parse_card

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CARDS_DIR = os.path.join(BASE_DIR, 'cards', 'approved')
PROMPTS_DIR = os.path.join(BASE_DIR, 'prompts')

def ingest_card(card_path, rating="SFW"):
    """
    Parses a character card and generates cold_open prompts from its first_mes
    and alternate_greetings.
    """
    if not os.path.exists(card_path):
        print(f"File not found: {card_path}")
        return

    try:
        card = parse_card(card_path)
    except Exception as e:
        print(f"Error parsing {card_path}: {e}")
        return

    card_name = card.get('name', 'UnknownCharacter')
    scenario = card.get('scenario', '')
    first_mes = card.get('first_mes', '')
    alt_greetings = card.get('alternate_greetings', [])
    personality = card.get('personality', '')

    scene_setup = f"You are {card_name}. Persona: {personality}. Scenario: {scenario}"
    
    prompts = []
    
    # 1. Main cold open from first message
    # In RP, the first message is often the *model's* turn, meaning the user must respond to trigger the model.
    # To benchmark as a "cold open", we provide the scene setup and a generic user turn that prompts the AI to speak the opening.
    # Or, the prompt is: Model plays Char. User turn triggers the situation. Let's make a generic user turn to trigger the character's opener.
    
    uid = str(uuid.uuid4())[:8]
    base_id = f"{rating.lower()}-cold-open-{card_name.lower().replace(' ', '-')}-{uid}"
    
    prompts.append({
        "id": f"{base_id}-1",
        "category": "cold_open",
        "rating": rating,
        "genre": ["roleplay"],
        "source": "character_card",
        "contributor": "community",
        "card_id": os.path.basename(card_path),
        "scene_setup": scene_setup,
        "user_turn": "*I enter the scene and look at you, waiting to see what you do.*",
        "expected_first_mes": first_mes, # For reference
        "scoring_dimensions": ["immersion", "prose_quality", "tone_matching", "scene_progression", "character_consistency"],
        "flags_to_watch": ["generic_opener", "ooc_break", "stalling"]
    })

    # Save logic
    out_dir = os.path.join(PROMPTS_DIR, rating.lower(), 'cold_open')
    os.makedirs(out_dir, exist_ok=True)
    
    for i, p in enumerate(prompts):
        out_file = os.path.join(out_dir, f"{p['id']}.json")
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(p, f, indent=2)
        print(f"Generated prompt: {out_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingest_card.py <path_to_card_json> [SFW|NSFW]")
    else:
        path = sys.argv[1]
        rating = sys.argv[2] if len(sys.argv) > 2 else "SFW"
        ingest_card(path, rating)
