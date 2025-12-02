import flet as ft
import sys
import threading
import io
import json
import os
import re
from bot import TradeBot
from database.interface import DatabaseInterface
from managers.config_manager import ConfigManager, PRESETS_DIR

# --- Constants ---
BOT_ITEMS_FILE = "config/bot_items.json"

class ConsoleRedirector(io.StringIO):
    def __init__(self, update_callback):
        super().__init__()
        self.update_callback = update_callback

    def write(self, message):
        if message.strip():
            self.update_callback(message)

    def flush(self):
        pass

class ItemData:
    def __init__(self, unique_name, localized_name, category, sub_category):
        self.unique_name = unique_name
        self.localized_name = localized_name
        self.category = category
        self.sub_category = sub_category
        match = re.match(r"T(\d+)_", unique_name)
        self.tier = int(match.group(1)) if match else 0
        if "@" in unique_name:
            try:
                self.enchant = int(unique_name.split("@")[1])
            except:
                self.enchant = 0
        else:
            self.enchant = 0

class ItemListPanel(ft.Container):
    def __init__(self, title, button_text, button_icon, button_color, on_action_click, on_item_click, item_icon):
        super().__init__()
        self.expand = True
        self.padding = 10
        self.bgcolor = ft.Colors.BLACK12
        self.border_radius = 10
        self.border = ft.border.all(1, ft.Colors.GREY_800)
        self.on_action_click = on_action_click
        self.on_item_click = on_item_click
        self.item_icon = item_icon
        self.current_items = []

        self.action_btn = ft.ElevatedButton(
            text=button_text, icon=button_icon, bgcolor=button_color, color=ft.Colors.WHITE,
            on_click=self.trigger_action, width=200
        )
        self.count_text = ft.Text("0 items", size=12, color=ft.Colors.GREY_400)
        self.item_list = ft.ListView(expand=True, spacing=2)

        self.content = ft.Column([
            ft.Text(title, weight=ft.FontWeight.BOLD, size=16),
            ft.Divider(height=10, thickness=1),
            ft.Row([self.action_btn, self.count_text], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(content=self.item_list, expand=True, bgcolor=ft.Colors.BLACK26, border_radius=5, padding=5)
        ])

    def update_list(self, items):
        self.current_items = items
        self.item_list.controls.clear()
        display_limit = 100
        for i, item in enumerate(items):
            if i >= display_limit:
                self.item_list.controls.append(ft.Text(f"... {len(items) - display_limit} more", size=12, italic=True))
                break
            self.item_list.controls.append(
                ft.ListTile(
                    leading=ft.Icon(self.item_icon, size=16, color=ft.Colors.GREY_400),
                    title=ft.Text(item.localized_name, size=14, weight=ft.FontWeight.BOLD),
                    subtitle=ft.Text(item.unique_name, size=10, color=ft.Colors.GREY_500, font_family="Consolas"),
                    dense=True, hover_color=ft.Colors.GREY_900,
                    on_click=lambda e, it=item: self.on_item_click(it)
                )
            )
        self.count_text.value = f"{len(items)} items"
        if self.item_list.page:
            self.item_list.update()
            self.count_text.update()

    def trigger_action(self, e):
        self.on_action_click(self.current_items)

class PresetManager(ft.Column):
    def __init__(self, config_manager):
        super().__init__()
        self.expand = True
        self.config = config_manager
        self.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        
        self.raw_json = self.load_json_data()
        self.all_item_objects = self.parse_items(self.raw_json)
        self.preset_set = set()

        self.selected_cat = None
        self.selected_sub = None
        self.selected_tiers = set()
        self.selected_enchants = set()

        self.cat_row = ft.Row(wrap=True, spacing=5, run_spacing=5)
        self.load_category_chips()
        self.sub_row = ft.Row(wrap=True, spacing=5, run_spacing=5)
        self.tier_row = ft.Row(wrap=True, spacing=5, run_spacing=5, controls=[ft.Chip(label=ft.Text(f"T{t}"), on_select=self.on_tier_toggle, data=t) for t in [4, 5, 6, 7, 8]])
        self.enchant_row = ft.Row(wrap=True, spacing=5, run_spacing=5, controls=[ft.Chip(label=ft.Text(f".{e}"), on_select=self.on_enchant_toggle, data=e) for e in [0, 1, 2, 3, 4]])

        self.left_panel = ItemListPanel("Available", "Add Filtered", ft.Icons.ADD, ft.Colors.GREEN_700, self.add_items_bulk, self.add_single_item, ft.Icons.ADD_CIRCLE_OUTLINE)
        self.right_panel = ItemListPanel("In Preset", "Remove Filtered", ft.Icons.DELETE, ft.Colors.RED_700, self.remove_items_bulk, self.remove_single_item, ft.Icons.HIGHLIGHT_OFF)

        self.preset_dropdown = ft.Dropdown(
            label="Select Preset", 
            width=250, 
            text_size=14, 
            content_padding=10, 
            dense=True,
            filled=True,
            bgcolor=ft.Colors.BLACK26,
            border_color=ft.Colors.GREY_800
        )
        self.update_preset_dropdown()

        self.filename_input = ft.TextField(label="Save as", suffix_text=".json", text_size=14, expand=True, content_padding=10, dense=True)
        
        filter_container = ft.Container(content=ft.Column([
            ft.Text("Filters", weight=ft.FontWeight.BOLD),
            ft.Text("Category:", size=12, color=ft.Colors.GREY_500), self.cat_row,
            ft.Text("Sub-Category:", size=12, color=ft.Colors.GREY_500), self.sub_row,
            ft.Row([ft.Column([ft.Text("Tier:", size=12, color=ft.Colors.GREY_500), self.tier_row]), ft.Column([ft.Text("Enchant:", size=12, color=ft.Colors.GREY_500), self.enchant_row])], vertical_alignment=ft.CrossAxisAlignment.START)
        ]), padding=15, bgcolor=ft.Colors.BLACK12, border_radius=10, border=ft.border.all(1, ft.Colors.GREY_800))

        self.controls = [
            ft.Container(content=ft.Row([
                ft.Text("Load:", weight=ft.FontWeight.BOLD), self.preset_dropdown, 
                ft.ElevatedButton("Load", icon=ft.Icons.UPLOAD_FILE, on_click=self.load_preset_click),
                ft.ElevatedButton("Delete", icon=ft.Icons.DELETE_FOREVER, on_click=self.delete_preset_click, bgcolor=ft.Colors.RED_900, color="white"),
                ft.VerticalDivider(width=20, color=ft.Colors.GREY_700),
                ft.Text("Save:", weight=ft.FontWeight.BOLD), self.filename_input,
                ft.ElevatedButton("Save", icon=ft.Icons.SAVE, on_click=self.save_preset_click, bgcolor=ft.Colors.GREEN_700, color="white")
            ]), padding=10, bgcolor=ft.Colors.BLACK26, border_radius=5),
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
            filter_container,
            ft.Divider(height=10),
            ft.Row([self.left_panel, ft.VerticalDivider(width=1, color=ft.Colors.GREY_800), self.right_panel], expand=True)
        ]
        self.apply_filters()

    def load_json_data(self):
        if not os.path.exists(BOT_ITEMS_FILE): return {}
        try:
            with open(BOT_ITEMS_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}

    def parse_items(self, json_data):
        objects = []
        for cat, sub_cats in json_data.items():
            for sub, items in sub_cats.items():
                if isinstance(items, dict):
                    for uid, name in items.items(): objects.append(ItemData(uid, name, cat, sub))
                elif isinstance(items, list):
                    for uid in items: objects.append(ItemData(uid, uid, cat, sub))
        return objects

    def load_category_chips(self):
        self.cat_row.controls = [ft.Chip(label=ft.Text(cat), on_select=self.on_cat_toggle, data=cat) for cat in self.raw_json.keys()]

    def update_preset_dropdown(self):
        files = self.config.get_presets_list()
        self.preset_dropdown.options = []
        for f in files:
            self.preset_dropdown.options.append(ft.dropdown.Option(f))
        if self.preset_dropdown.page: self.preset_dropdown.update()

    def on_cat_toggle(self, e):
        self.selected_cat = e.control.data if e.control.selected else None
        for chip in self.cat_row.controls: chip.selected = (chip.data == self.selected_cat)
        if self.cat_row.page: self.cat_row.update()
        self.selected_sub = None
        self.reload_sub_categories()
        self.apply_filters()

    def reload_sub_categories(self):
        self.sub_row.controls.clear()
        if self.selected_cat:
            sub_cats = self.raw_json.get(self.selected_cat, {}).keys()
            for sub in sub_cats: self.sub_row.controls.append(ft.Chip(label=ft.Text(sub), on_select=self.on_sub_toggle, data=sub))
        if self.sub_row.page: self.sub_row.update()

    def on_sub_toggle(self, e):
        self.selected_sub = e.control.data if e.control.selected else None
        for chip in self.sub_row.controls: chip.selected = (chip.data == self.selected_sub)
        if self.sub_row.page: self.sub_row.update()
        self.apply_filters()

    def on_tier_toggle(self, e):
        t = e.control.data
        if e.control.selected: self.selected_tiers.add(t)
        else: self.selected_tiers.discard(t)
        self.apply_filters()

    def on_enchant_toggle(self, e):
        en = e.control.data
        if e.control.selected: self.selected_enchants.add(en)
        else: self.selected_enchants.discard(en)
        self.apply_filters()

    def apply_filters(self):
        filtered = []
        for item in self.all_item_objects:
            if self.selected_cat and item.category != self.selected_cat: continue
            if self.selected_sub and item.sub_category != self.selected_sub: continue
            if self.selected_tiers and item.tier not in self.selected_tiers: continue
            if self.selected_enchants and item.enchant not in self.selected_enchants: continue
            filtered.append(item)
        
        self.left_panel.update_list([i for i in filtered if i.unique_name not in self.preset_set])
        self.right_panel.update_list([i for i in filtered if i.unique_name in self.preset_set])

    def add_single_item(self, item): self.preset_set.add(item.unique_name); self.apply_filters()
    def remove_single_item(self, item): self.preset_set.discard(item.unique_name); self.apply_filters()
    def add_items_bulk(self, items): 
        for i in items: self.preset_set.add(i.unique_name)
        self.apply_filters()
    def remove_items_bulk(self, items): 
        for i in items: self.preset_set.discard(i.unique_name)
        self.apply_filters()

    def load_preset_click(self, e):
        fname = self.preset_dropdown.value
        if not fname: return
        try:
            with open(os.path.join(PRESETS_DIR, fname), "r") as f: self.preset_set = set(json.load(f))
            self.filename_input.value = fname.replace(".json", "")
            if self.filename_input.page: self.filename_input.update()
            self.apply_filters()
        except Exception as ex: print(ex)

    def delete_preset_click(self, e):
        fname = self.preset_dropdown.value
        if not fname: return
        try:
            os.remove(os.path.join(PRESETS_DIR, fname))
            self.update_preset_dropdown()
            self.preset_dropdown.value = None
            if self.preset_dropdown.page: self.preset_dropdown.update()
        except: pass

    def save_preset_click(self, e):
        name = self.filename_input.value
        if not name: return
        try:
            with open(os.path.join(PRESETS_DIR, f"{name}.json"), "w") as f: json.dump(list(self.preset_set), f, indent=4)
            self.update_preset_dropdown()
        except: pass

class ConfigTab(ft.Column):
    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.expand = True
        self.padding = 20

        # Input Fields
        self.min_profit = ft.TextField(
            label="Min Profit Rate (%)", 
            value=str(self.config.get("min_profit_rate")), 
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor=ft.Colors.BLACK,
            border_color=ft.Colors.GREY_800
        )
        self.stop_silver = ft.TextField(
            label="Stop if Silver <", 
            value=str(self.config.get("min_silver_to_stop")), 
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor=ft.Colors.BLACK,
            border_color=ft.Colors.GREY_800
        )
        
        # Preset Dropdowns
        presets = self.config.get_presets_list()
        
        self.check_preset = ft.Dropdown(
            label="Preset for Checking Prices", 
            options=[ft.dropdown.Option(f) for f in presets],
            value=self.config.get("check_price_preset"),
            filled=True,
            bgcolor=ft.Colors.BLACK,
            border_color=ft.Colors.GREY_800,
            color=ft.Colors.WHITE,
            width=400
        )
        self.buy_preset = ft.Dropdown(
            label="Preset for Buying Items", 
            options=[ft.dropdown.Option(f) for f in presets],
            value=self.config.get("buy_items_preset"),
            filled=True,
            bgcolor=ft.Colors.BLACK,
            border_color=ft.Colors.GREY_800,
            color=ft.Colors.WHITE,
            width=400
        )

        self.save_btn = ft.ElevatedButton("Save Configuration", icon=ft.Icons.SAVE, on_click=self.save_config, bgcolor=ft.Colors.GREEN_700, color="white")

        self.controls = [
            ft.Text("Bot Configuration", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Container(content=ft.Column([
                ft.Text("General Settings", size=16, weight=ft.FontWeight.BOLD),
                self.min_profit,
                self.stop_silver,
                ft.Divider(),
                ft.Text("Active Presets", size=16, weight=ft.FontWeight.BOLD),
                self.check_preset,
                self.buy_preset,
                ft.Divider(),
                self.save_btn
            ], spacing=20), width=600)
        ]

    def refresh_presets(self):
        presets = self.config.get_presets_list()
        self.check_preset.options = [ft.dropdown.Option(f) for f in presets]
        self.buy_preset.options = [ft.dropdown.Option(f) for f in presets]
        if self.page:
            self.check_preset.update()
            self.buy_preset.update()

    def save_config(self, e):
        try:
            self.config.set("min_profit_rate", float(self.min_profit.value))
            self.config.set("min_silver_to_stop", int(self.stop_silver.value))
            self.config.set("check_price_preset", self.check_preset.value)
            self.config.set("buy_items_preset", self.buy_preset.value)
            
            self.page.snack_bar = ft.SnackBar(ft.Text("Configuration Saved!"))
            self.page.snack_bar.open = True
            self.page.update()
        except Exception as ex:
            print(ex)

def main(page: ft.Page):
    page.title = "Albion Trade Bot Manager"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1200
    page.window_height = 900
    page.padding = 10

    config_manager = ConfigManager()

    log_output = ft.TextField(value="--- Bot Logs ---\n", multiline=True, read_only=True, text_size=12, expand=True, bgcolor=ft.Colors.BLACK38, border_color=ft.Colors.GREY_800, text_style=ft.TextStyle(font_family="Consolas"))
    
    def log_msg(msg): 
        if page: log_output.value += msg; page.update()
    
    sys.stdout = ConsoleRedirector(log_msg)
    sys.stderr = ConsoleRedirector(log_msg)

    bot = None
    def run_bot(task):
        nonlocal bot
        if not bot:
            try: bot = TradeBot(db=DatabaseInterface())
            except: pass
        if bot: threading.Thread(target=task, daemon=True).start()

    dash = ft.Container(content=ft.Column([
        ft.Text("Dashboard", size=24, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        ft.Row([
            ft.ElevatedButton("Check Prices", icon=ft.Icons.SEARCH, on_click=lambda e: run_bot(bot.check_price), bgcolor=ft.Colors.INDIGO_600, color="white"),
            ft.ElevatedButton("Buy Items", icon=ft.Icons.SHOPPING_CART, on_click=lambda e: run_bot(bot.buy_items), bgcolor=ft.Colors.TEAL_600, color="white")
        ]),
        ft.Divider(),
        ft.Container(content=log_output, expand=True, border_radius=5)
    ]), padding=10, expand=True)

    config_tab = ConfigTab(config_manager)
    preset_manager = PresetManager(config_manager)
    
    # Hook to refresh presets dropdown when switching tabs
    def on_tab_change(e):
        if e.control.selected_index == 2: # Config Tab
            config_tab.refresh_presets()
        elif e.control.selected_index == 1: # Presets Tab
            preset_manager.update_preset_dropdown()

    t = ft.Tabs(selected_index=0, expand=True, on_change=on_tab_change, tabs=[
        ft.Tab(text="Dashboard", icon=ft.Icons.DASHBOARD, content=dash),
        ft.Tab(text="Items Presets", icon=ft.Icons.LIST_ALT, content=ft.Container(content=preset_manager, padding=5)),
        ft.Tab(text="Bot Configuration", icon=ft.Icons.SETTINGS, content=config_tab)
    ])
    page.add(t)

if __name__ == "__main__":
    ft.app(target=main)