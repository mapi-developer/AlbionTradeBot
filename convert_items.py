import json
import os

# Configuration
BOT_ITEMS_FILE = "config/bot_items.json"
GAME_ITEMS_FILE = "config/items.json"

def load_json(path):
    if not os.path.exists(path):
        print(f"Error: {path} not found.")
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    print("Loading files...")
    bot_data = load_json(BOT_ITEMS_FILE)
    game_data = load_json(GAME_ITEMS_FILE)

    if not bot_data or not game_data:
        return

    # 1. Build Lookup Table (UniqueName -> EN-US Name)
    print("Building name lookup...")
    name_lookup = {}
    for item in game_data:
        u_name = item.get("UniqueName")
        loc_names = item.get("LocalizedNames")
        if u_name and loc_names:
            name_lookup[u_name] = loc_names.get("EN-US", u_name)

    # 2. Convert List Structure to Dictionary Structure
    print("Converting bot_items...")
    new_bot_data = {}

    for category, subcats in bot_data.items():
        new_bot_data[category] = {}
        for subcat, items_list in subcats.items():
            new_bot_data[category][subcat] = {}
            
            # Handle if it's a list (current format)
            if isinstance(items_list, list):
                for item_id in items_list:
                    # Get readable name, default to ID if missing
                    readable_name = name_lookup.get(item_id, item_id)
                    new_bot_data[category][subcat][item_id] = readable_name
            
            # Handle if it's already a dict (future proofing)
            elif isinstance(items_list, dict):
                new_bot_data[category][subcat] = items_list

    # 3. Save Result
    try:
        with open(BOT_ITEMS_FILE, "w", encoding="utf-8") as f:
            json.dump(new_bot_data, f, indent=4, ensure_ascii=False)
        print(f"Success! {BOT_ITEMS_FILE} has been converted to Dictionary format.")
    except Exception as e:
        print(f"Error saving file: {e}")

if __name__ == "__main__":
    main()