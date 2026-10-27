"""Read and write the JSON files in the data folder."""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


# read a json file, return default if it is not there
def load(filename, default=None):
    path = DATA_DIR / filename
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# write a dict into a json file
def save(filename, data):
    path = DATA_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
