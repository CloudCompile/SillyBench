import os
import json
from datetime import datetime
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS_DIR = os.path.join(BASE_DIR, 'results', 'runs')
LEADERBOARD_PATH = os.path.join(BASE_DIR, 'results', 'leaderboard.json')

def aggregate_results():
    if not os.path.exists(RUNS_DIR):
        print(f"Runs directory not found at {RUNS_DIR}")
        return

    models_data = defaultdict(lambda: {
        "runs": 0,
        "run_ids": [],
        "sfw_scores": [],
        "nsfw_scores": [],
        "categories": defaultdict(list),
        "flags": defaultdict(int)
    })

    total_runs = 0

    for filename in os.listdir(RUNS_DIR):
        if not filename.endswith('.json'):
            continue
        
        filepath = os.path.join(RUNS_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                run_doc = json.load(f)
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON file: {filename}")
                continue
        
        model_name = run_doc.get("model", "unknown")
        run_id = run_doc.get("run_id", filename)
        aggregates = run_doc.get("aggregates", {})
        
        stats = models_data[model_name]
        stats["runs"] += 1
        stats["run_ids"].append(run_id)
        
        sfw = aggregates.get("sfw_overall", 0)
        nsfw = aggregates.get("nsfw_overall", 0)
        
        if sfw > 0: stats["sfw_scores"].append(sfw)
        if nsfw > 0: stats["nsfw_scores"].append(nsfw)
        
        total_runs += 1

        # Aggregate categories and flags to calculate best/worst/most common later
        for cat, score in aggregates.get("by_category", {}).items():
            if score > 0: stats["categories"][cat].append(score)
            
        for flag, count in aggregates.get("flag_frequency", {}).items():
            stats["flags"][flag] += count

    # Compile the final leaderboard entries
    leaderboard_models = []
    for model_name, stats in models_data.items():
        avg_sfw = sum(stats["sfw_scores"]) / len(stats["sfw_scores"]) if stats["sfw_scores"] else 0
        avg_nsfw = sum(stats["nsfw_scores"]) / len(stats["nsfw_scores"]) if stats["nsfw_scores"] else 0
        combined = (avg_sfw + avg_nsfw) / 2 if (avg_sfw > 0 and avg_nsfw > 0) else (avg_sfw or avg_nsfw)
        
        # Calculate best and worst category
        cat_averages = {cat: sum(scores)/len(scores) for cat, scores in stats["categories"].items() if len(scores) > 0}
        best_cat = max(cat_averages, key=cat_averages.get) if cat_averages else "N/A"
        worst_cat = min(cat_averages, key=cat_averages.get) if cat_averages else "N/A"
        
        # Calculate most common flag
        most_common_flag = max(stats["flags"], key=stats["flags"].get) if stats["flags"] else "None"
        
        leaderboard_models.append({
            "model": model_name,
            "runs": stats["runs"],
            "sfw_overall": round(avg_sfw, 2),
            "nsfw_overall": round(avg_nsfw, 2),
            "combined_overall": round(combined, 2),
            "best_category": best_cat,
            "worst_category": worst_cat,
            "most_common_flag": most_common_flag,
            "run_ids": stats["run_ids"]
        })

    # Sort descending by combined overall
    leaderboard_models.sort(key=lambda x: x["combined_overall"], reverse=True)

    leaderboard = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_runs": total_runs,
        "models": leaderboard_models
    }

    os.makedirs(os.path.dirname(LEADERBOARD_PATH), exist_ok=True)
    with open(LEADERBOARD_PATH, 'w', encoding='utf-8') as f:
        json.dump(leaderboard, f, indent=2)
        
    print(f"Aggregated {total_runs} runs into leaderboard.json")

if __name__ == "__main__":
    aggregate_results()
