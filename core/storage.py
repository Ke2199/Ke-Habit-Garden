"""Read and write the JSON files in the data folder."""
import json
import shutil
import sys
from pathlib import Path

# where the starting data files live (inside the app bundle when packaged)
_BUNDLED_DATA = Path(__file__).parent / "data"

# a packaged .app cannot save files inside itself, so we keep the
# real data in the user's Documents folder instead
if getattr(sys, "frozen", False):
    DATA_DIR = Path.home() / "Documents" / "Habit Garden"
    # first run: copy the starting data out of the app bundle
    if not DATA_DIR.exists():
        shutil.copytree(_BUNDLED_DATA, DATA_DIR)
else:
    DATA_DIR = _BUNDLED_DATA


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
