import os
import json
import uuid
import sys
import re
from datetime import datetime
from utils.pollinations import OpenAICompatibleAPI, PollinationsAPI
from utils.template import render_template

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTS_DIR = os.path.join(BASE_DIR, 'prompts')
JUDGE_DIR = os.path.join(BASE_DIR, 'judge')
RESULTS_DIR = os.path.join(BASE_DIR, 'results', 'runs')

def run_bench(target_model="gpt-4o-mini", target_provider="openai", target_endpoint="", target_api_key=""):
    run_id = f"run-{str(uuid.uuid4())[:8]}"
    date_str = datetime.utcnow().isoformat()
    
    # 1. Load judge config
    with open(os.path.join(JUDGE_DIR, 'judge_prompt.md'), 'r', encoding='utf-8') as f:
        base_judge_prompt = f.read()
    with open(os.path.join(JUDGE_DIR, 'dimensions_sfw.json'), 'r') as f:
        dim_sfw = f.read()
    with open(os.path.join(JUDGE_DIR, 'dimensions_nsfw.json'), 'r') as f:
        dim_nsfw = f.read()
    with open(os.path.join(JUDGE_DIR, 'flags.json'), 'r') as f:
        flags_json = f.read()
        
    # 2. Iterate prompts
    results = []
    
    # Using Pollinations for Judge and the custom API object for the Target
    # We'll use Pollinations entirely if APIs are omit for a demo
    target_api = PollinationsAPI() if not target_endpoint else OpenAICompatibleAPI(target_api_key, target_endpoint)
    judge_api = PollinationsAPI() # Default free tier DeepSeek representation
    
    for rating in ['sfw', 'nsfw']:
        rdir = os.path.join(PROMPTS_DIR, rating)
        if not os.path.exists(rdir): continue
        
        for category in os.listdir(rdir):
            cdir = os.path.join(rdir, category)
            if not os.path.isdir(cdir): continue
            
            for file in os.listdir(cdir):
                if not file.endswith('.json'): continue
                
                pf = os.path.join(cdir, file)
                with open(pf, 'r', encoding='utf-8') as f:
                    pdata = json.load(f)
                    
                print(f"Testing Prompt: {pdata['id']} ({rating}/{category})")
                
                # Render prompt
                sys_msg = pdata['scene_setup']
                usr_msg = pdata['user_turn']
                usr_msg = render_template(usr_msg, char_name="Char", user_name="User")
                
                # --- CALL TARGET MODEL ---
                target_messages = [
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": usr_msg}
                ]
                
                print(f"  -> Generating response with {target_model}...")
                target_response = target_api.call(model=target_model, messages=target_messages)
                if not target_response:
                    print("  -> ERROR generating response")
                    continue
                    
                # --- CALL JUDGE MODEL ---
                jp = base_judge_prompt.replace('{{RATING_TYPE}}', rating.upper())
                jp = jp.replace('{{SCENE_SETUP}}', sys_msg)
                jp = jp.replace('{{USER_TURN}}', usr_msg)
                jp = jp.replace('{{MODEL_RESPONSE}}', target_response)
                
                dims_to_use = dim_sfw if rating == 'sfw' else dim_nsfw
                jp = jp.replace('{{DIMENSIONS_JSON}}', dims_to_use)
                jp = jp.replace('{{FLAGS_JSON}}', flags_json)
                
                print(f"  -> Evaluating with DeepSeek Judge...")
                judge_resp = judge_api.call(model="deepseek", messages=[
                    {"role": "system", "content": jp},
                    {"role": "user", "content": "Please output the evaluation."}
                ])
                
                # Parse judge output
                if judge_resp:
                    match = re.search(r'```json\s*(.*?)\s*```', judge_resp, re.DOTALL | re.IGNORECASE)
                    if match:
                        try:
                            judge_data = json.loads(match.group(1))
                            
                            results.append({
                                "prompt_id": pdata['id'],
                                "response": target_response,
                                "judge_thinking": judge_data.get('thinking', ''),
                                "scores": judge_data.get('scores', {}),
                                "flags": judge_data.get('flags', []),
                                "overall": judge_data.get('overall', 0),
                                "summary": judge_data.get('summary', '')
                            })
                            print(f"  -> Scored Overall: {judge_data.get('overall', 0)}")
                        except json.JSONDecodeError:
                            print("  -> ERROR Parsing JSON from Judge")
                    else:
                        print("  -> ERROR No JSON block found in Judge response")

    # Aggregate simple stats
    sfw_sum = 0
    nsfw_sum = 0
    sfw_count = 0
    nsfw_count = 0
    
    for r in results:
        pid = r['prompt_id']
        overall = r.get('overall', 0)
        if pid.startswith('sfw'):
            sfw_sum += overall
            sfw_count += 1
        else:
            nsfw_sum += overall
            nsfw_count += 1

    run_doc = {
        "run_id": run_id,
        "model": target_model,
        "model_provider": target_provider,
        "judge_model": "deepseek",
        "judge_provider": "pollinations",
        "date": date_str,
        "contributor": "local_runner",
        "commit_hash": "untracked",
        "results": results,
        "aggregates": {
            "sfw_overall": (sfw_sum / sfw_count) if sfw_count else 0,
            "nsfw_overall": (nsfw_sum / nsfw_count) if nsfw_count else 0,
            "by_category": {},
            "by_dimension": {},
            "flag_frequency": {}
        }
    }
    
    os.makedirs(RESULTS_DIR, exist_ok=True)
    out_path = os.path.join(RESULTS_DIR, f"{run_id}-{target_model}.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(run_doc, f, indent=2)
        
    print(f"\nSaved Run Benchmark Results to {out_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_bench(target_model=sys.argv[1])
    else:
        run_bench()
