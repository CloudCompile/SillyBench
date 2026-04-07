# SillyBench

SillyBench is a community-driven, reproducible Roleplay evaluation benchmark for LLMs. 

## Features
- **Separated Tracks**: Dedicated SFW and NSFW scoring streams—never blended.
- **Auditable Quality**: Leverages `deepseek-r1` as an objective AI evaluator with public reasoning blocks.
- **Anti-gaming safeguards**: Standardized schema structure, fixed baseline prompts.
- **Community First**: Character cards and prompts can be submitted via Pull Request, aggregated natively via GitHub Actions.

## Quickstart
To evaluate a model you host locally or via OpenAI-Compatible API:
```bash
python scripts/run_bench.py "my-custom-model" 
```
This produces a `result.json` which can be PR'd to this repo.

## Evaluating New Character Cards
To add a Character Card into the testing suite from SillyTavern:
```bash
python scripts/screen_cards.py path/to/my/card.png
# and then
python scripts/ingest_card.py cards/approved/sfw/my-card.json
```

## Directory Structure
- `cards/`: V2/V3 character cards serving as prompt generators.
- `judge/`: LLM evaluator prompts mapping directly to rigid dimensions and flags.
- `prompts/`: Curated test arrays mapping to categorical tests (e.g., `cold_open`, `tone_pivot`).
- `results/`: Submitted community outputs & the live auto-generated leaderboard.
- `scripts/`: Benchmark engine codebase.
- `schema/`: Enforced JSON schemas for CI actions.
Just an expirimental benchmark
