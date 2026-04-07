import os
import json
import fnmatch
from jsonschema import validate, ValidationError

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_DIR = os.path.join(BASE_DIR, 'schema')

def load_schema(schema_name):
    path = os.path.join(SCHEMA_DIR, schema_name)
    with open(path, 'r') as f:
        return json.load(f)

def validate_dir(directory, schema_name, pattern='*.json'):
    schema = load_schema(schema_name)
    if not os.path.exists(directory):
        return True
        
    all_valid = True
    for root, _, files in os.walk(directory):
        for filename in fnmatch.filter(files, pattern):
            filepath = os.path.join(root, filename)
            with open(filepath, 'r') as f:
                try:
                    data = json.load(f)
                    validate(instance=data, schema=schema)
                    print(f"PASS: {filename} against {schema_name}")
                except json.JSONDecodeError as e:
                    print(f"FAIL (Parse Error): {filepath} - {e}")
                    all_valid = False
                except ValidationError as e:
                    print(f"FAIL (Schema Validation): {filepath} - {e.message}")
                    all_valid = False
    return all_valid

if __name__ == "__main__":
    import sys
    print("Validating Run Results...")
    runs_valid = validate_dir(os.path.join(BASE_DIR, 'results', 'runs'), 'run.schema.json')
    
    print("\nValidating SFW Prompts...")
    sfw_valid = validate_dir(os.path.join(BASE_DIR, 'prompts', 'sfw'), 'prompt.schema.json')
    
    print("\nValidating NSFW Prompts...")
    nsfw_valid = validate_dir(os.path.join(BASE_DIR, 'prompts', 'nsfw'), 'prompt.schema.json')
    
    if runs_valid and sfw_valid and nsfw_valid:
        print("\nAll files passed schema validation.")
        sys.exit(0)
    else:
        print("\nValidation failed.")
        sys.exit(1)
