import os, sys
import json

if getattr(sys, 'frozen', False):
    # If running as a compiled .exe, use the executable's directory
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # If running as a script, use the project root relative to this file
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_json_config(filename):
    """Loads a JSON file from the config directory."""
    config_path = os.path.join(BASE_DIR, 'config/static', filename) 
    with open(config_path, 'r', encoding="utf-8") as f:
        return json.load(f)

class SettingsManager:
    MOUSE_POSITIONS = load_json_config('mouse_positions.json')
    ITEM_DATA = load_json_config('items.json')
    CAPTURE_POSITIONS = load_json_config('capture_positions.json')
    ITEMS_BLACK_MARKET = load_json_config('black_market_items_dictionary.json')
    
    ORDER_PRICE_CHECK_ACCOUNTS = [
        {"email": "matvey4a.alt.1@gmail.com", "password": "matvey4a_alt"},
    ]

    SPECIAL_ITEMS_BM = {
        "2452": 2,
        "2831": 2,
        "8473": 1,
        "6239": 2,
        "6843": 2,
        "1997": 1,
        "2149": 2,
        "3383": 2,
        "3410": 2,
        "3437": 2,
        "3990": 1,
        "4018": 1,
        "4046": 1,
        "4598": 2,
        "4625": 2,
        "4652": 2,
        "2910": 3,
        "9076": 3,
        "8875": 3,
        "9277": 3,
        "6440": 3,
        "7848": 3,
        "8069": 3,
        "8674": 3,
        "9478": 3,
        "7647": 3,
        "2300": 3,
        "7446": 3,
        "7245": 3,
        "7044": 3,
        "6641": 3,
    }

    SPECIAL_ITEMS = {
        "Shield": 1,
        "Mercenary Hood": 1,
        "Mercenary Jacket": 1,
        "Mercenary Shoes": 1,
        "Broadsword": 1,
        "Tome of Spells": 2,
        "Cape": 2,
        "Bag": 2,
        "Soldier Helmet": 2,
        "Soldier Armor": 2,
        "Soldier Boots": 2,
        "Scholar Cowl": 2,
        "Scholar Robe": 2,
        "Scholar Sandals": 2,
        "Bow": 2,
        "Fire Staff": 2,
        "Torch": 3,
        "Crossbow": 3,
        "Cursed Staff": 3,
        "Fire Staff": 3,
        "Frost Staff": 3,
        "Arcane Staff": 3,
        "Holy Staff": 3,
        "Nature Staff": 3,
        "Dagger": 3,
        "Spear": 3,
        "Battleaxe": 3,
        "Quarterstaff": 3,
        "Hammer": 3,
        "Mace": 3,
        "Brawler Gloves": 3,
        "Prowling Staff": 3,
    }

    MARKETS = [
        "fort_sterling",
        "lymhurst",
        "bridgewatch",
        "martlock",
        "thetford",
        "black_market",
    ]

    AVALIABLE_LANGUAGES = [
        "EN-US",
        "DE-DE",
        "FR-FR",
        "RU-RU",
        "PL-PL",
        "ES-ES",
        "PT-BR",
        "IT-IT",
        "ZH-CN",
        "KO-KR",
        "JA-JP",
        "ZH-TW",
        "ID-ID",
        "TR-TR",
        "AR-SA"
    ]

    CITIES = {
        "caerleon": "Caerleon",
        "martlock": "Martlock",
        "lymhurst": "Lymhurst",
        "fort_sterling": "Fort Sterling",
        "bridgewatch": "Bridgewatch",
        "thetford": "Thetford",
        "brecilien": "Brecilien",
    }

    DEFAULT_SETTINGS = {
        "general": {
            "min_silver": 1000000,
            "game_language": "RU-RU",
            "buy_mode": "order",
        },
        "fast_buy": {
            "min_profit_rate": 25,
            "default_build_amount": 15,
            "presets": {
                "fort_sterling": "",
                "lymhurst": "",
                "bridgewatch": "",
                "martlock": "",
                "thetford": "",
                "caerleon": "",
                "brecilien": ""
            },
            "buy_logic": []
        },
        "order_buy": {
            "min_profit_rate": 60,
            "default_build_amount": 25,
            "presets": {
                "fort_sterling": "",
                "lymhurst": "",
                "bridgewatch": "",
                "martlock": "",
                "thetford": "",
                "caerleon": "",
                "brecilien": ""
            },
            "buy_logic": []
        },
    }

    API_URL = "https://trade-backend-service-1054089939982.europe-west4.run.app"
    GOOGLE_CLIENT_ID = "1054089939982-e2umo92u5p7mh4gjm3hvknddprenho3k.apps.googleusercontent.com"
    DISCORD_CLIENT_ID = "1447721013260456058"

    LOCAL_AUTH_PORT = 5000
    LOCAL_REDIRECT_URI = f"http://127.0.0.1:{LOCAL_AUTH_PORT}/oauth/callback"

    ITEMS_JSON_URL = "https://raw.githubusercontent.com/ao-data/ao-bin-dumps/master/formatted/items.json"
    CACHE_FILE = os.path.join(BASE_DIR, "config/static", "items.json")
    BOT_ITEMS_FILE = os.path.join(BASE_DIR, "config/static", "bot_items.json")

    BOT_LOOP_FILE = os.path.join(BASE_DIR, "config/settings", "bot_loop.json")
    SETTINGS_FILE = os.path.join(BASE_DIR, "config/settings", "settings.json")
    PRESETS_DIR = os.path.join(BASE_DIR, "config/settings", "presets")
    LOGS_DIR = os.path.join(BASE_DIR, "config/logs")

    TRAVALER_BANNERS = [
        # QUAD HD
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "1.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "2.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "3.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "4.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "5.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "6.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "7.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "8.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "9.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "10.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "11.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "12.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "13.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "14.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "15.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "16.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "17.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "18.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "19.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "20.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "21.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "22.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "23.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "24.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "25.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "26.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "27.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "28.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "29.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "30.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "31.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "32.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "33.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "34.png"),
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "35.png"),
        # FULL HD
        os.path.join(BASE_DIR, "config\\static\\img\\travaler_icons", "36.png"),
    ]

    def __init__(self):
        self.ensure_directories()
        self.settings = self.load_settings()

    def ensure_directories(self):
        if not os.path.exists("config"):
            os.makedirs("config")
        if not os.path.exists(self.PRESETS_DIR):
            os.makedirs(self.PRESETS_DIR)

    def load_settings(self):
        if not os.path.exists(self.SETTINGS_FILE):
            self.save_settings(self.DEFAULT_SETTINGS)
            return self.DEFAULT_SETTINGS
        try:
            with open(self.SETTINGS_FILE, "r") as f:
                return json.load(f)
        except:
            return self.DEFAULT_SETTINGS
        
    def save_settings(self, new_settings):
        try:
            with open(self.SETTINGS_FILE, "w") as f:
                json.dump(new_settings, f, indent=4)
            self.settings = new_settings
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def get(self, key):
        return self.settings.get(key, self.DEFAULT_SETTINGS.get(key))

    def set(self, key, value):
        #print("save settings")
        self.settings[key] = value
        self.save_settings(self.settings)

    def get_presets_list(self):
        if not os.path.exists(self.PRESETS_DIR):
            return []
        return [f for f in os.listdir(self.PRESETS_DIR) if f.endswith(".json")]

    def load_bot_loop(self):
        if not os.path.exists(self.BOT_LOOP_FILE):
            return []
        try:
            with open(self.BOT_LOOP_FILE, "r") as f:
                return json.load(f)
        except:
            return []

    def save_bot_loop(self, loop_data):
        try:
            with open(self.BOT_LOOP_FILE, "w") as f:
                json.dump(loop_data, f, indent=4)
        except Exception as e:
            print(f"Error saving bot loop: {e}")

    def get_logs(self):
        """Returns a list of log filenames, sorted by newest first."""
        if not os.path.exists(self.LOGS_DIR):
            return []
        try:
            files = [f for f in os.listdir(self.LOGS_DIR) if f.endswith('.json')]
            files.sort(reverse=True)
            return files
        except Exception as e:
            print(f"Error listing logs: {e}")
            return []

    def get_log(self, filename):
        """Returns the content of a specific log file as a list/dict."""
        path = os.path.join(self.LOGS_DIR, filename)
        if not os.path.exists(path):
            return []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading log {filename}: {e}")
            return []
        
    def delete_log(self, filename):
        """Deletes a specific log file."""
        path = os.path.join(self.LOGS_DIR, filename)
        if os.path.exists(path):
            try:
                os.remove(path)
                return True
            except Exception as e:
                print(f"Error deleting log {filename}: {e}")
                return False
        return False