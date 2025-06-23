import json
from pathlib import Path

CONFIG_PATH = Path(__file__).with_name('default_config.json')

with open(CONFIG_PATH, 'r') as f:
    DEFAULT_PARAMS = json.load(f)
