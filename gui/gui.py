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
from gui.modules.popup import show_popup

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
        self.padding = 5
        self.bgcolor = ft.Colors.BLACK12
        self.border_radius = 10
        self.border = ft.border.all(1, ft.Colors.GREY_800)
        self.on_action_click = on_action_click
        self.on_item_click = on_item_click
        self.item_icon = item_icon
        self.current_items = []

        self.action_btn = ft.ElevatedButton(
            text=button_text, icon=button_icon, bgcolor=button_color, color=ft.Colors.WHITE,
            on_click=self.trigger_action, height=30, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5))
        )
        self.count_text = ft.Text("0 items", size=11, color=ft.Colors.GREY_400)
        self.item_list = ft.ListView(expand=True, spacing=1, item_extent=35, auto_scroll=False)

        self.content = ft.Column([
            ft.Text(title, weight=ft.FontWeight.BOLD, size=14),
            ft.Divider(height=5, thickness=1),
            ft.Row([self.action_btn, self.count_text], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(content=self.item_list, expand=True, bgcolor=ft.Colors.BLACK26, border_radius=5, padding=2, height=420) # 12 items * 35 extent
        ], spacing=5)

    def update_list(self, items):
        self.current_items = items
        self.item_list.controls.clear()
        display_limit = 100
        for i, item in enumerate(items):
            if i >= display_limit:
                self.item_list.controls.append(ft.Text(f"... {len(items) - display_limit} more", size=11, italic=True))
                break
            self.item_list.controls.append(
                ft.ListTile(
                    leading=ft.Icon(self.item_icon, size=14, color=ft.Colors.GREY_400),
                    title=ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Text(item.localized_name, size=12, weight=ft.FontWeight.BOLD, overflow=ft.TextOverflow.ELLIPSIS, no_wrap=True),
                                ft.Text(item.unique_name, size=9, color=ft.Colors.GREY_500, font_family="Consolas", overflow=ft.TextOverflow.ELLIPSIS, no_wrap=True),
                            ], spacing=2, alignment=ft.MainAxisAlignment.CENTER),
                            width=250 # Set a fixed width for the text column
                        ),
                        ft.Image(
                            src=f"https://render.albiononline.com/v1/item/{item.unique_name}",
                            width=40, height=40, fit=ft.ImageFit.CONTAIN,
                            border_radius=ft.border_radius.all(5),
                        )
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    dense=True, hover_color=ft.Colors.GREY_900,
                    on_click=lambda e, it=item: self.on_item_click(it),
                    content_padding=ft.padding.symmetric(vertical=0, horizontal=5)
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
        self.horizontal_alignment = ft.CrossAxisAlignment.STRETCH # Make children stretch to width
        self.spacing = 3 # Tight spacing (outside padding equivalent)
        self.padding = 20
        
        self.raw_json = self.load_json_data()
        self.all_item_objects = self.parse_items(self.raw_json)
        self.preset_set = set()

        self.selected_cat = None
        self.selected_sub = None
        self.selected_tiers = set()
        self.selected_enchants = set()

        self.cat_row = ft.Row(wrap=True, spacing=2, run_spacing=2)
        self.load_category_chips()
        self.sub_row = ft.Row(wrap=True, spacing=2, run_spacing=2)
        
        # Helper to create compact chips
        def create_chip(text, data, callback):
            return ft.Chip(
                label=ft.Text(text, size=11), 
                on_select=callback, 
                data=data,
                label_padding=ft.padding.symmetric(horizontal=4)
            )

        self.tier_row = ft.Row(wrap=True, spacing=2, run_spacing=2, controls=[create_chip(f"T{t}", t, self.on_tier_toggle) for t in [4, 5, 6, 7, 8]])
        self.enchant_row = ft.Row(wrap=True, spacing=2, run_spacing=2, controls=[create_chip(f".{e}", e, self.on_enchant_toggle) for e in [0, 1, 2, 3, 4]])

        self.left_panel = ItemListPanel("Available", "Add Filtered", ft.Icons.ADD, ft.Colors.GREEN_700, self.add_items_bulk, self.add_single_item, ft.Icons.ADD_CIRCLE_OUTLINE)
        self.right_panel = ItemListPanel("In Preset", "Remove Filtered", ft.Icons.DELETE, ft.Colors.RED_700, self.remove_items_bulk, self.remove_single_item, ft.Icons.HIGHLIGHT_OFF)

        self.preset_dropdown = ft.Dropdown(
            label="Select Preset", 
            width=200, 
            text_size=12, 
            content_padding=8, 
            dense=True,
            filled=True,
            bgcolor=ft.Colors.BLACK, # Opaque Black Background
            border_color=ft.Colors.GREY_800
        )
        self.update_preset_dropdown()

        self.filename_input = ft.TextField(label="Save as", suffix_text=".json", text_size=12, expand=True, dense=True, height=35)
        
        # Compact Filter Container with reduced internal padding
        filter_container = ft.Container(content=ft.Column([
            ft.Row([
                ft.Text("Filters", weight=ft.FontWeight.BOLD, size=14),
                ft.VerticalDivider(width=10, color=ft.Colors.TRANSPARENT),
                ft.Row([ft.Text("Tier:", size=11, color=ft.Colors.GREY_500), self.tier_row], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.VerticalDivider(width=10, color=ft.Colors.TRANSPARENT),
                ft.Row([ft.Text("Ench:", size=11, color=ft.Colors.GREY_500), self.enchant_row], vertical_alignment=ft.CrossAxisAlignment.CENTER)
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Divider(height=2, color=ft.Colors.GREY_900),
            ft.Column([ft.Text("Category:", size=11, color=ft.Colors.GREY_500), self.cat_row], spacing=0),
            ft.Column([ft.Text("Sub-Cat:", size=11, color=ft.Colors.GREY_500), self.sub_row], spacing=0),
        ], spacing=2), padding=5, bgcolor=ft.Colors.BLACK12, border_radius=5, border=ft.border.all(1, ft.Colors.GREY_800), margin=10)

        self.controls = [
            ft.Container(content=ft.Row([
                ft.Text("Load:", weight=ft.FontWeight.BOLD, size=12), self.preset_dropdown, 
                ft.IconButton(icon=ft.Icons.UPLOAD_FILE, on_click=self.load_preset_click, tooltip="Load"),
                ft.IconButton(icon=ft.Icons.DELETE_FOREVER, on_click=self.delete_preset_click, icon_color=ft.Colors.RED_400, tooltip="Delete"),
                ft.VerticalDivider(width=10, color=ft.Colors.GREY_700),
                ft.Text("Save:", weight=ft.FontWeight.BOLD, size=12), self.filename_input,
                ft.IconButton(icon=ft.Icons.SAVE, on_click=self.save_preset_click, icon_color=ft.Colors.GREEN_400, tooltip="Save")
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER), padding=5, bgcolor=ft.Colors.BLACK26, border_radius=5, margin=10),
            filter_container,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT), # Padding
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
        self.cat_row.controls = [ft.Chip(label=ft.Text(cat, size=11), on_select=self.on_cat_toggle, data=cat, label_padding=ft.padding.symmetric(horizontal=4)) for cat in self.raw_json.keys()]

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
            for sub in sub_cats: 
                self.sub_row.controls.append(ft.Chip(label=ft.Text(sub, size=11), on_select=self.on_sub_toggle, data=sub, label_padding=ft.padding.symmetric(horizontal=4)))
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
        if not fname:
            show_popup(self.page, "Please select a preset to load.", is_error=True)
            return
        try:
            with open(os.path.join(PRESETS_DIR, fname), "r") as f: 
                self.preset_set = set(json.load(f))
            
            self.filename_input.value = fname.replace(".json", "")
            if self.filename_input.page: 
                self.filename_input.update()
            
            self.apply_filters()
            #
            show_popup(self.page, f"Preset '{fname}' loaded successfully!")
        except Exception as ex: 
            print(ex)
            show_popup(self.page, f"Error loading preset: {ex}", is_error=True)

    def save_preset_click(self, e):
        name = self.filename_input.value
        if not name: 
            show_popup(self.page, "Please enter a filename to save.", is_error=True)
            return
        try:
            with open(os.path.join(PRESETS_DIR, f"{name}.json"), "w") as f: 
                json.dump(list(self.preset_set), f, indent=4)
            
            self.update_preset_dropdown()
            #
            show_popup(self.page, f"Preset '{name}.json' saved successfully!")
        except Exception as ex:
            show_popup(self.page, f"Error saving preset: {ex}", is_error=True)

    def delete_preset_click(self, e):
        fname = self.preset_dropdown.value
        if not fname: return
        try:
            os.remove(os.path.join(PRESETS_DIR, fname))
            self.update_preset_dropdown()
            self.preset_dropdown.value = None
            if self.preset_dropdown.page: self.preset_dropdown.update()
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
            border_color=ft.Colors.GREY_800,
            width=200 # 15% of 1200 is 180, 200 looks better
        )
        self.stop_silver = ft.TextField(
            label="Stop if Silver <", 
            value=str(self.config.get("min_silver_to_stop")), 
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor=ft.Colors.BLACK,
            border_color=ft.Colors.GREY_800,
            width=200 # 15% of 1200 is 180, 200 looks better
        )
        
        # Preset Dropdowns
        presets = self.config.get_presets_list()
        
        self.buy_fort_sterling = ft.Dropdown(
            label="Fort Sterling", 
            options=[ft.dropdown.Option(f) for f in presets],
            value=self.config.get("buy_items_preset_fort_sterling"),
            label_style=ft.TextStyle(size=12),
            filled=True,
            bgcolor=ft.Colors.BLACK,
            border_color=ft.Colors.GREY_800,
            color=ft.Colors.WHITE,
            width=300,
            enable_filter=True,
            editable=True,
        )
        self.buy_lymhurst = ft.Dropdown(
            label="Lymhurst", 
            options=[ft.dropdown.Option(f) for f in presets],
            value=self.config.get("buy_items_preset_lymhurst"),
            label_style=ft.TextStyle(size=12),
            filled=True,
            bgcolor=ft.Colors.BLACK,
            border_color=ft.Colors.GREY_800,
            color=ft.Colors.WHITE,
            width=300,
            enable_filter=True,
            editable=True,
        )
        self.buy_bridgewatch = ft.Dropdown(
            label="Bridgewatch", 
            options=[ft.dropdown.Option(f) for f in presets],
            value=self.config.get("buy_items_preset_bridgewatch"),
            label_style=ft.TextStyle(size=12),
            filled=True,
            bgcolor=ft.Colors.BLACK,
            border_color=ft.Colors.GREY_800,
            color=ft.Colors.WHITE,
            width=300,
            enable_filter=True,
            editable=True,
        )
        self.buy_martlock = ft.Dropdown(
            label="Martlock", 
            options=[ft.dropdown.Option(f) for f in presets],
            value=self.config.get("buy_items_preset_martlock"),
            label_style=ft.TextStyle(size=12),
            filled=True,
            bgcolor=ft.Colors.BLACK,
            border_color=ft.Colors.GREY_800,
            color=ft.Colors.WHITE,
            width=300,
            enable_filter=True,
            editable=True,
        )
        self.buy_thetford = ft.Dropdown(
            label="Thetford", 
            options=[ft.dropdown.Option(f) for f in presets],
            value=self.config.get("buy_items_preset_thetford"),
            label_style=ft.TextStyle(size=12),
            filled=True,
            bgcolor=ft.Colors.BLACK,
            border_color=ft.Colors.GREY_800,
            color=ft.Colors.WHITE,
            width=300,
            enable_filter=True,
            editable=True,
        )
        self.buy_caerleon = ft.Dropdown(
            label="Caerleon", 
            options=[ft.dropdown.Option(f) for f in presets],
            value=self.config.get("buy_items_preset_caerleon"),
            label_style=ft.TextStyle(size=12),
            filled=True,
            bgcolor=ft.Colors.BLACK,
            border_color=ft.Colors.GREY_800,
            color=ft.Colors.WHITE,
            width=300,
            enable_filter=True,
            editable=True,
        )
        self.buy_brecilien = ft.Dropdown(
            label="Brecilien", 
            options=[ft.dropdown.Option(f) for f in presets],
            value=self.config.get("buy_items_preset_brecilien"),
            label_style=ft.TextStyle(size=12),
            filled=True,
            bgcolor=ft.Colors.BLACK,
            border_color=ft.Colors.GREY_800,
            color=ft.Colors.WHITE,
            width=300,
            enable_filter=True,
            editable=True,
        )

        self.save_btn = ft.ElevatedButton("Save Configuration", icon=ft.Icons.SAVE, on_click=self.save_config, bgcolor=ft.Colors.GREEN_700, color="white")

        # --- Layout ---
        left_column = ft.Container(
            content=ft.Column([
                ft.Text("Active Presets", size=16, weight=ft.FontWeight.BOLD),
                self.buy_fort_sterling, self.buy_lymhurst, self.buy_bridgewatch,
                self.buy_martlock, self.buy_thetford, self.buy_caerleon, self.buy_brecilien,
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
            padding=20,
            border=ft.border.all(1, ft.Colors.GREY_800),
            border_radius=10,
            expand=1 # 20% width
        )

        right_column = ft.Container(
            content=ft.Column([
                ft.Text("General Settings", size=16, weight=ft.FontWeight.BOLD),
                self.min_profit,
                self.stop_silver,
            ], spacing=20),
            padding=20,
            border=ft.border.all(1, ft.Colors.GREY_800),
            border_radius=10,
            expand=4 # 80% width
        )

        self.controls = [
            ft.Text("Bot Configuration", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Column([
                ft.Row([left_column, right_column], spacing=20, vertical_alignment=ft.CrossAxisAlignment.START),
                ft.Row([self.save_btn], alignment=ft.MainAxisAlignment.START)
            ], expand=True)
        ]

    def refresh_presets(self):
        presets = self.config.get_presets_list()
        self.buy_fort_sterling.options = [ft.dropdown.Option(f) for f in presets]
        self.buy_lymhurst.options = [ft.dropdown.Option(f) for f in presets]
        self.buy_bridgewatch.options = [ft.dropdown.Option(f) for f in presets]
        self.buy_martlock.options = [ft.dropdown.Option(f) for f in presets]
        self.buy_thetford.options = [ft.dropdown.Option(f) for f in presets]
        self.buy_caerleon.options = [ft.dropdown.Option(f) for f in presets]
        self.buy_brecilien.options = [ft.dropdown.Option(f) for f in presets]
        
        if self.page:
            self.buy_fort_sterling.update()
            self.buy_lymhurst.update()
            self.buy_bridgewatch.update()
            self.buy_martlock.update()
            self.buy_thetford.update()
            self.buy_caerleon.update()
            self.buy_brecilien.update()

    def save_config(self, e):
        try:
            self.config.set("min_profit_rate", float(self.min_profit.value))
            self.config.set("min_silver_to_stop", int(self.stop_silver.value))
            self.config.set("buy_items_preset_fort_sterling", self.buy_fort_sterling.value)
            self.config.set("buy_items_preset_lymhurst", self.buy_lymhurst.value)
            self.config.set("buy_items_preset_bridgewatch", self.buy_bridgewatch.value)
            self.config.set("buy_items_preset_martlock", self.buy_martlock.value)
            self.config.set("buy_items_preset_thetford", self.buy_thetford.value)
            self.config.set("buy_items_preset_caerleon", self.buy_caerleon.value)
            self.config.set("buy_items_preset_brecilien", self.buy_brecilien.value)
            
            # Replaced manual SnackBar with popup call
            show_popup(self.page, "Configuration Saved Successfully!")
            
            self.page.update()
        except ValueError:
            show_popup(self.page, "Invalid input: Please enter numbers for profit/silver.", is_error=True)
        except Exception as ex:
            print(ex)
            show_popup(self.page, f"Error saving settings: {ex}", is_error=True)

def main(page: ft.Page):
    page.title = "Albion Trade Bot Manager"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1200
    page.window_height = 900
    page.padding = 10

    config_manager = ConfigManager()

    log_output = ft.TextField(value="--- Bot Logs ---\n", multiline=True, read_only=True, text_size=12, expand=True, bgcolor=ft.Colors.BLACK38, border_color=ft.Colors.GREY_800, text_style=ft.TextStyle(font_family="Consolas"))
    
    def log_msg(msg): 
        if page: log_output.value += "\n"+msg; page.update()
    
    sys.stdout = ConsoleRedirector(log_msg)
    sys.stderr = ConsoleRedirector(log_msg)

    bot = None
    def run_bot(task_name: str):
        nonlocal bot
        if not bot:
            try:
                print("Initializing bot...")
                bot = TradeBot(db=DatabaseInterface())
                print("Bot initialized.")
            except Exception as e:
                print(f"Error initializing bot: {e}")
                return
        
        if bot:
            task_to_run = getattr(bot, task_name, None)
            if callable(task_to_run):
                threading.Thread(target=task_to_run, daemon=True).start()

    dash = ft.Container(content=ft.Column([
        ft.Text("Dashboard", size=24, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        ft.Row([
            ft.ElevatedButton("Check Prices", icon=ft.Icons.SEARCH, on_click=lambda e: run_bot("check_price"), bgcolor=ft.Colors.INDIGO_600, color="white"),
            ft.ElevatedButton("Buy Items", icon=ft.Icons.SHOPPING_CART, on_click=lambda e: run_bot("buy_items"), bgcolor=ft.Colors.TEAL_600, color="white")
        ]),
        ft.Divider(),
        ft.Container(content=log_output, expand=True, border_radius=5)
    ]), padding=20, expand=True)

    config_tab = ConfigTab(config_manager)
    preset_manager = PresetManager(config_manager)
    
    # Hook to refresh presets dropdown when switching tabs
    def on_tab_change(e):
        if e.control.selected_index == 2: # Config Tab
            config_tab.refresh_presets()
        elif e.control.selected_index == 1: # Presets Tab
            preset_manager.update_preset_dropdown()

    t = ft.Tabs(selected_index=0, expand=True, on_change=on_tab_change, tabs=[
        ft.Tab(text="Dashboard", icon=ft.Icons.DASHBOARD, content=ft.Column([dash], scroll=ft.ScrollMode.AUTO, expand=True)),
        ft.Tab(text="Items Presets", icon=ft.Icons.LIST_ALT, content=ft.Column([preset_manager], scroll=ft.ScrollMode.AUTO, expand=True)),
        ft.Tab(text="Bot Configuration", icon=ft.Icons.SETTINGS, content=ft.Column([config_tab], scroll=ft.ScrollMode.AUTO, expand=True))
    ])
    page.add(t)

if __name__ == "__main__":
    ft.app(target=main)