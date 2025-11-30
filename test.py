import json
import re
import os

def generate_readable_names_dict():
    # Paths to your files
    items_path = 'config/items.json'
    base_names_path = 'config/black_market_base_names.json'
    output_path = 'config/black_market_lookup.json'

    if not os.path.exists(items_path) or not os.path.exists(base_names_path):
        print("Error: Input files not found.")
        return

    print("Loading data...")
    with open(items_path, 'r', encoding='utf-8') as f:
        all_items = json.load(f)

    with open(base_names_path, 'r', encoding='utf-8') as f:
        target_base_names = set(json.load(f))

    # Prefixes to strip from English names
    # These correspond to T1 - T8
    tier_prefixes = [
        "Beginner's ", "Novice's ", "Journeyman's ", 
        "Adept's ", "Expert's ", "Master's ", 
        "Grandmaster's ", "Elder's "
    ]

    final_dict = {}

    print("Processing items...")
    
    # We loop through all items to find a match for our base names
    for item in all_items:
        unique_name = item.get("UniqueName", "")
        if not unique_name:
            continue

        # Skip enchanted items (@1, @2) to ensure we get the basic name
        if "@" in unique_name:
            continue

        # Extract the base name from the current item (e.g., T4_HEAD_CLOTH -> HEAD_CLOTH)
        # We look for the pattern "T" + digit + "_"
        match = re.match(r"T\d+_(.+)", unique_name)
        if not match:
            continue
        
        current_base_name = match.group(1)

        # If this item represents one of the base names we want
        if current_base_name in target_base_names:
            
            # Get the English name
            loc_names = item.get("LocalizedNames", {})
            eng_name = None
            if loc_names != None:
                eng_name = loc_names.get("EN-US")
            if not eng_name:
                continue

            # Strip the Tier prefix
            clean_name = eng_name
            for prefix in tier_prefixes:
                if clean_name.startswith(prefix):
                    clean_name = clean_name.replace(prefix, "")
                    break # Stop after finding the matching prefix

            # Add to dictionary
            # We overwrite if it exists, which is fine because "Expert's X" and "Master's X" 
            # both reduce to "X", so the value remains the same.
            final_dict[current_base_name] = clean_name

    # Save the new dictionary
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_dict, f, indent=2, sort_keys=True)

    print(f"Success! Created dictionary with {len(final_dict)} items at {output_path}")

if __name__ == "__main__":
    generate_readable_names_dict()