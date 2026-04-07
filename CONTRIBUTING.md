# Contributing to SillyBench

SillyBench relies deeply on a community dataset. If you have run an open weights model that isn't yet cataloged or want to see your 2-billion parameter model stacked up against Sonnet and GPT-4, you are in the right place!

## 1. How to submit a Benchmark Run
1. Fork this repository.
2. Ensure you have the `jsonschema` python dependency.
3. Use the supplied `scripts/run_bench.py` and connect it to your model. Wait for the `deepseek-r1` evaluation to finish processing. 
4. The script yields `run-[uuid]-[model].json` in the `/results/runs/` folder.
5. Commit this file on a new branch.
6. Submit a Pull Request.

**Note:** The PR CI will run `validate_pr.yml`. Your file will be structurally verified against the schema. Upon PR approval, the `aggregate.py` job will automatically ingest your scores updating the top-level Leaderboard markdown without requiring a separate PR limit!

## 2. Submitting Character Cards
Community character cards fuel the benchmark engine!
1. Ensure your card passes standard dimensions (coherent description, strong starting message).
2. Execute `python scripts/screen_cards.py <card>`.
3. If it is rejected, view the specific reasoning flag and make adjustments.
4. If it approves, open a Pull request adding the JSON format of your card to `/cards/raw/`. 

When accepted by maintainers, the ingestion script dynamically strips the valid greeting components into core scenario blocks (`prompts/`).

## 3. Creating Prompts Directly 
You can bypass cards and contribute hand-written scene prompts. Copy the structural framework inside the curated `/prompts/` directories and submit! Do not change schema keys.