import json
import os

def load_json_config(filename):
    """Loads a JSON file from the config directory."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', filename)
    with open(config_path, 'r', encoding="utf-8") as f:
        return json.load(f)

# In bot.py (or another manager)

# Load the constant data when the application starts
MOUSE_POSITIONS = load_json_config('mouse_positions.json')
ITEM_DATA = load_json_config('items.json')
CAPTURE_POSITIONS = load_json_config('capture_positions.json')
ITEMS_TO_BUY = load_json_config('items_to_buy.json')
ITEMS_BLACK_MARKET = load_json_config('black_market_items_dictionary.json')
LANGUAGE = "EN-US"
