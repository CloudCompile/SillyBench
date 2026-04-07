import os
import json
import uuid
import sys
import re
from utils.card_parser import parse_card
from utils.pollinations import PollinationsAPI

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDS_DIR = os.path.join(BASE_DIR, 'cards')
JUDGE_DIR = os.path.join(BASE_DIR, 'judge')

def screen_cards(card_path):
    if not os.path.exists(card_path):
        print(f"File not found: {card_path}")
        return

    try:
        card = parse_card(card_path)
    except Exception as e:
        print(f"Error parsing {card_path}: {e}")
        return

    print(f"Screening card: {card.get('name', 'Unknown')}...")
    
    with open(os.path.join(JUDGE_DIR, 'card_quality_prompt.md'), 'r', encoding='utf-8') as f:
        judge_sys_prompt = f.read()
    
    judge_sys_prompt = judge_sys_prompt.replace('{{CARD_JSON}}', json.dumps(card, indent=2))
    
    api = PollinationsAPI() # using public free tier if available or expects API key
    
    messages = [
        {"role": "system", "content": judge_sys_prompt},
        {"role": "user", "content": "Please output the evaluation for this card."}
    ]

    response = api.call(model="deepseek-r1", messages=messages)
    
    # parse the JSON block at the end
    match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL | re.IGNORECASE)
    if not match:
        print("Failed to parse JSON from judge response.")
        print("Raw Response:", response)
        return
    
    result_json = match.group(1)
    
    try:
        verdict = json.loads(result_json)
        passed = verdict.get('passed', False)
        
        filename = os.path.basename(card_path)
        if passed:
            # Assume SFW, though real implementation would categorize
            dest_dir = os.path.join(CARDS_DIR, 'approved', 'sfw')
        else:
            dest_dir = os.path.join(CARDS_DIR, 'rejected')
        
        os.makedirs(dest_dir, exist_ok=True)
        new_path = os.path.join(dest_dir, filename)
        
        # Move the card
        import shutil
        shutil.copy(card_path, new_path)
        
        # Save rationale
        reason_path = os.path.join(dest_dir, f"{os.path.splitext(filename)[0]}_screening.json")
        with open(reason_path, 'w', encoding='utf-8') as f:
            json.dump(verdict, f, indent=2)
            
        status = "PASSED" if passed else "REJECTED"
        print(f"Result: {status}. Saved reasoning at: {reason_path}")
        
    except json.JSONDecodeError as e:
        print(f"Error parsing judge output as JSON: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python screen_cards.py <path_to_card_json>")
    else:
        screen_cards(sys.argv[1])
