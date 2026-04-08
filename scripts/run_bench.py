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


def evaluate_constraints(response, prompt_data):
    """Return deterministic constraint checks for a prompt response."""
    text = (response or "").lower()
    report = {
        "required_terms": {"passed": [], "missed": []},
        "forbidden_terms": {"triggered": []},
        "max_words": {"limit": None, "actual": None, "passed": True},
    }

    required_terms = prompt_data.get("required_terms", [])
    forbidden_terms = prompt_data.get("forbidden_terms", [])
    max_words = prompt_data.get("max_words")

    for term in required_terms:
        if term.lower() in text:
            report["required_terms"]["passed"].append(term)
        else:
            report["required_terms"]["missed"].append(term)

    for term in forbidden_terms:
        if term.lower() in text:
            report["forbidden_terms"]["triggered"].append(term)

    if isinstance(max_words, int) and max_words > 0:
        actual_words = len((response or "").split())
        report["max_words"] = {
            "limit": max_words,
            "actual": actual_words,
            "passed": actual_words <= max_words,
        }

    violations = 0
    violations += len(report["required_terms"]["missed"])
    violations += len(report["forbidden_terms"]["triggered"])
    if report["max_words"]["limit"] is not None and not report["max_words"]["passed"]:
        violations += 1

    report["violations"] = violations
    return report

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

                hard_constraints = pdata.get('hard_constraints', [])
                forbidden_patterns = pdata.get('forbidden_patterns', [])
                hard_constraints_text = "\n".join([f"- {c}" for c in hard_constraints]) if hard_constraints else "- None"
                forbidden_patterns_text = "\n".join([f"- {p}" for p in forbidden_patterns]) if forbidden_patterns else "- None"
                jp = jp.replace('{{HARD_CONSTRAINTS}}', hard_constraints_text)
                jp = jp.replace('{{FORBIDDEN_PATTERNS}}', forbidden_patterns_text)
                
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
                            
                            constraint_report = evaluate_constraints(target_response, pdata)
                            final_flags = list(judge_data.get('flags', []))
                            final_overall = float(judge_data.get('overall', 0))

                            if constraint_report["violations"] > 0:
                                if "constraint_violation" not in final_flags:
                                    final_flags.append("constraint_violation")
                                # Deterministic penalty: each violation reduces by 0.4, floor at 1.0
                                final_overall = max(1.0, round(final_overall - (0.4 * constraint_report["violations"]), 2))

                            results.append({
                                "prompt_id": pdata['id'],
                                "response": target_response,
                                "judge_thinking": judge_data.get('thinking', ''),
                                "scores": judge_data.get('scores', {}),
                                "flags": final_flags,
                                "overall": final_overall,
                                "summary": judge_data.get('summary', '')
                                ,"constraint_report": constraint_report
                            })
                            print(f"  -> Scored Overall: {final_overall}")
                        except json.JSONDecodeError:
                            print("  -> ERROR Parsing JSON from Judge")
                    else:
                        print("  -> ERROR No JSON block found in Judge response")

    # Build prompt metadata map for category tracking
    prompt_metadata = {}
    for rating in ['sfw', 'nsfw']:
        rdir = os.path.join(PROMPTS_DIR, rating)
        if os.path.exists(rdir):
            for category in os.listdir(rdir):
                cdir = os.path.join(rdir, category)
                if os.path.isdir(cdir):
                    for file in os.listdir(cdir):
                        if file.endswith('.json'):
                            pf = os.path.join(cdir, file)
                            with open(pf, 'r') as f:
                                pdata = json.load(f)
                                prompt_metadata[pdata['id']] = {'rating': rating, 'category': category}

    # Aggregate stats with categorical and dimensional breakdowns
    sfw_sum = 0
    nsfw_sum = 0
    sfw_count = 0
    nsfw_count = 0
    by_category = {}
    by_dimension = {}
    flag_freq = {}
    
    for r in results:
        pid = r['prompt_id']
        overall = r.get('overall', 0)
        scores = r.get('scores', {})
        flags = r.get('flags', [])
        
        # Track by rating
        if pid.startswith('sfw'):
            sfw_sum += overall
            sfw_count += 1
        else:
            nsfw_sum += overall
            nsfw_count += 1
        
        # Track by category
        if pid in prompt_metadata:
            category = prompt_metadata[pid]['category']
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(overall)
        
        # Track by dimension
        for dim, score in scores.items():
            if dim not in by_dimension:
                by_dimension[dim] = []
            by_dimension[dim].append(score)
        
        # Track flags
        for flag in flags:
            flag_freq[flag] = flag_freq.get(flag, 0) + 1
    
    # Average out lists
    by_category_avg = {cat: round(sum(scores) / len(scores), 2) for cat, scores in by_category.items()}
    by_dimension_avg = {dim: round(sum(scores) / len(scores), 2) for dim, scores in by_dimension.items()}

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
            "sfw_overall": round((sfw_sum / sfw_count) if sfw_count else 0, 2),
            "nsfw_overall": round((nsfw_sum / nsfw_count) if nsfw_count else 0, 2),
            "by_category": by_category_avg,
            "by_dimension": by_dimension_avg,
            "flag_frequency": flag_freq
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
