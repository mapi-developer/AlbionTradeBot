import flet as ft
import re, os, json
from managers.config import ConfigManager, PRESETS_DIR, BOT_ITEMS_FILE
from .settings import Settings
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from components.popup import show_popup

THEME_PANEL_BG = "#294D7C"  # Main container color
THEME_INNER_BG = "#203064"  # Inner cards/inputs color
THEME_BORDER_C = ft.Colors.with_opacity(0.1, ft.Colors.WHITE)


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
    """
    Reusable panel for displaying lists of items (Used in Presets tab).
    Updated to match Dashboard theme.
    """

    def __init__(
        self,
        title,
        button_text,
        button_icon,
        button_color,
        on_action_click,
        on_item_click,
        item_icon,
    ):
        super().__init__()
        self.expand = True
        self.padding = 5
        self.bgcolor = THEME_PANEL_BG
        self.border_radius = 10
        self.border = ft.border.all(1, THEME_BORDER_C)
        self.on_action_click = on_action_click
        self.on_item_click = on_item_click
        self.item_icon = item_icon
        self.current_items = []

        self.action_btn = ft.ElevatedButton(
            text=button_text,
            icon=button_icon,
            bgcolor=button_color,
            color=ft.Colors.WHITE,
            on_click=self.trigger_action,
            height=30,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5)),
        )
        self.count_text = ft.Text("0 items", size=11, color=ft.Colors.WHITE70)
        self.item_list = ft.ListView(
            expand=True, spacing=1, item_extent=35, auto_scroll=False
        )

        self.content = ft.Column(
            [
                ft.Text(
                    title, weight=ft.FontWeight.BOLD, size=14, color=ft.Colors.WHITE
                ),
                ft.Divider(height=5, thickness=1, color=ft.Colors.WHITE24),
                ft.Row(
                    [self.action_btn, self.count_text],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(
                    content=self.item_list,
                    expand=True,
                    bgcolor=THEME_INNER_BG,
                    border_radius=5,
                    padding=2,
                    height=420,
                ),
            ],
            spacing=5,
        )

    def update_list(self, items):
        self.current_items = items

        # 🛠️ FIX: Build a new list locally first to prevent AssertionError during rapid updates
        new_controls = []
        display_limit = 100

        for i, item in enumerate(items):
            if i >= display_limit:
                new_controls.append(
                    ft.Text(
                        f"... {len(items) - display_limit} more",
                        size=11,
                        italic=True,
                        color=ft.Colors.WHITE54,
                    )
                )
                break

            new_controls.append(
                ft.ListTile(
                    leading=ft.Icon(self.item_icon, size=14, color=ft.Colors.WHITE54),
                    title=ft.Row(
                        [
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text(
                                            item.localized_name,
                                            size=12,
                                            weight=ft.FontWeight.BOLD,
                                            overflow=ft.TextOverflow.ELLIPSIS,
                                            no_wrap=True,
                                            color=ft.Colors.WHITE,
                                        ),
                                        ft.Text(
                                            item.unique_name,
                                            size=9,
                                            color=ft.Colors.WHITE54,
                                            font_family="Consolas",
                                            overflow=ft.TextOverflow.ELLIPSIS,
                                            no_wrap=True,
                                        ),
                                    ],
                                    spacing=2,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                                width=250,
                            ),
                            ft.Image(
                                src=f"https://render.albiononline.com/v1/item/{item.unique_name}",
                                width=40,
                                height=40,
                                fit=ft.ImageFit.CONTAIN,
                                border_radius=ft.border_radius.all(5),
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    dense=True,
                    hover_color="#2A3C55",
                    on_click=lambda e, it=item: self.on_item_click(it),
                    content_padding=ft.padding.symmetric(vertical=0, horizontal=5),
                )
            )

        # 🛠️ FIX: Atomic assignment to .controls
        self.item_list.controls = new_controls
        self.count_text.value = f"{len(items)} items"

        if self.item_list.page:
            self.item_list.update()
            self.count_text.update()

    def trigger_action(self, e):
        self.on_action_click(self.current_items)


class Presets(ft.Column):
    def __init__(self, config: ConfigManager, page: ft.Page, settings: Settings):
        super().__init__()
        self.settings = settings
        self.expand = True
        self.config = config
        self.page = page
        self.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        self.spacing = 3
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

        self.search_input = ft.TextField(
            label="Search by name...",
            suffix_icon=ft.Icons.SEARCH,
            text_size=12,
            dense=True,
            height=35,
            on_change=lambda e: self.apply_filters(),
            bgcolor=THEME_INNER_BG,
            border_color=ft.Colors.TRANSPARENT,
        )

        def create_chip(text, data, callback):
            return ft.Chip(
                label=ft.Text(text, size=11, color="#FFFFFF"),
                on_select=callback,
                data=data,
                label_padding=ft.padding.symmetric(horizontal=4),
                bgcolor=THEME_INNER_BG,
                # 🛠️ FIX: Use 'border' instead of 'border_side' or 'side'
                border_side=ft.BorderSide(width=0, color=ft.Colors.TRANSPARENT),
                selected_color="#1B223D",
            )

        def remove_filters(e):
            self.selected_cat = None
            self.selected_sub = None
            self.selected_tiers.clear()
            self.selected_enchants.clear()
            self.search_input.value = ""

            for chip in self.cat_row.controls:
                chip.selected = False
            for chip in self.tier_row.controls:
                chip.selected = False
            for chip in self.enchant_row.controls:
                chip.selected = False

            self.sub_row.controls.clear()

            if self.page:
                self.cat_row.update()
                self.sub_row.update()
                self.tier_row.update()
                self.enchant_row.update()
                self.search_input.update()
            self.apply_filters()

        self.tier_row = ft.Row(
            wrap=True,
            spacing=2,
            run_spacing=2,
            controls=[
                create_chip(f"T{t}", t, self.on_tier_toggle) for t in [4, 5, 6, 7, 8]
            ],
        )
        self.enchant_row = ft.Row(
            wrap=True,
            spacing=2,
            run_spacing=2,
            controls=[
                create_chip(f".{e}", e, self.on_enchant_toggle) for e in [0, 1, 2, 3, 4]
            ],
        )

        self.left_panel = ItemListPanel(
            "Available",
            "Add Filtered",
            ft.Icons.ADD,
            ft.Colors.GREEN_700,
            self.add_items_bulk,
            self.add_single_item,
            ft.Icons.ADD_CIRCLE_OUTLINE,
        )
        self.right_panel = ItemListPanel(
            "In Preset",
            "Remove Filtered",
            ft.Icons.DELETE,
            ft.Colors.RED_700,
            self.remove_items_bulk,
            self.remove_single_item,
            ft.Icons.HIGHLIGHT_OFF,
        )

        self.preset_dropdown = ft.Dropdown(
            label="Select Preset",
            width=200,
            text_size=12,
            content_padding=8,
            dense=True,
            bgcolor="#1e293b",
            border_color="#1e293b",
            fill_color=THEME_INNER_BG,
            filled=True,
        )
        self.update_preset_dropdown()

        self.filename_input = ft.TextField(
            label="Save as",
            suffix_text=".json",
            text_size=12,
            expand=True,
            dense=True,
            height=35,
            bgcolor=THEME_INNER_BG,
            border_color=ft.Colors.TRANSPARENT,
        )

        filter_container = ft.Container(
            content=ft.ResponsiveRow(
                controls=[
                    ft.Column(
                        controls=[
                            self.search_input,
                            ft.Row(
                                [
                                    ft.Text(
                                        "Tier:",
                                        size=11,
                                        color="#ffffff",
                                    ),
                                    self.tier_row,
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Row(
                                [
                                    ft.Text(
                                        "Ench:",
                                        size=11,
                                        color="#ffffff",
                                    ),
                                    self.enchant_row,
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ],
                        col={"md": 4},
                    ),
                    ft.Column(
                        [
                            ft.Column(
                                [
                                    ft.Text("Category:", size=11, color="#ffffff"),
                                    self.cat_row,
                                ],
                                spacing=0,
                            ),
                            ft.Column(
                                [
                                    ft.Text("Sub-Cat:", size=11, color="#ffffff"),
                                    self.sub_row,
                                ],
                                spacing=0,
                            ),
                        ],
                        spacing=2,
                        col={"md": 7},
                    ),
                    ft.Column(
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.REFRESH_ROUNDED,
                                icon_color=ft.Colors.WHITE,
                                tooltip="Remove Filters",
                                on_click=remove_filters,
                            )
                        ],
                        spacing=2,
                        col={"md": 0.5},
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=5,
            bgcolor=THEME_PANEL_BG,
            border_radius=5,
            border=ft.border.all(1, THEME_BORDER_C),
            margin=10,
        )

        self.controls = [
            ft.Container(
                content=ft.Row(
                    [
                        ft.Text(
                            "Load:",
                            weight=ft.FontWeight.BOLD,
                            size=16,
                            color=ft.Colors.WHITE,
                        ),
                        self.preset_dropdown,
                        ft.IconButton(
                            icon=ft.Icons.UPLOAD_FILE,
                            on_click=self.load_preset_click,
                            tooltip="Load",
                            icon_color=ft.Colors.WHITE,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_FOREVER,
                            on_click=self.delete_preset_click,
                            icon_color=ft.Colors.RED_400,
                            tooltip="Delete",
                        ),
                        ft.VerticalDivider(width=10, color=ft.Colors.WHITE24),
                        ft.Text(
                            "Save:",
                            weight=ft.FontWeight.BOLD,
                            size=16,
                            color=ft.Colors.WHITE,
                        ),
                        self.filename_input,
                        ft.IconButton(
                            icon=ft.Icons.SAVE,
                            on_click=self.save_preset_click,
                            icon_color=ft.Colors.GREEN_400,
                            tooltip="Save",
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=5,
                bgcolor=THEME_PANEL_BG,
                border_radius=5,
                margin=10,
            ),
            filter_container,
            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),  # Padding
            ft.Container(
                ft.Row(
                    [
                        self.left_panel,
                        ft.VerticalDivider(width=1, color=ft.Colors.TRANSPARENT),
                        self.right_panel,
                    ],
                    expand=True,
                ),
                expand=True,
                padding=ft.padding.only(10, 0, 10, 10),
            ),
        ]
        self.apply_filters()

    def load_json_data(self):
        if not os.path.exists(BOT_ITEMS_FILE):
            return {}
        try:
            with open(BOT_ITEMS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}

    def parse_items(self, json_data):
        objects = []
        for cat, sub_cats in json_data.items():
            for sub, items in sub_cats.items():
                if isinstance(items, dict):
                    for uid, name in items.items():
                        objects.append(ItemData(uid, name, cat, sub))
                elif isinstance(items, list):
                    for uid in items:
                        objects.append(ItemData(uid, uid, cat, sub))
        return objects

    def load_category_chips(self):
        self.cat_row.controls = [
            ft.Chip(
                label=ft.Text(cat, size=11, color="#FFFFFF"),
                on_select=self.on_cat_toggle,
                data=cat,
                label_padding=ft.padding.symmetric(horizontal=4),
                bgcolor=THEME_INNER_BG,
                border_side=ft.BorderSide(width=0, color=ft.Colors.TRANSPARENT),
                selected_color="#1B223D",
            )
            for cat in self.raw_json.keys()
        ]

    def update_preset_dropdown(self):
        files = self.config.get_presets_list()
        self.preset_dropdown.options = []
        for f in files:
            self.preset_dropdown.options.append(ft.dropdown.Option(f))
        if self.preset_dropdown.page:
            self.preset_dropdown.update()

    def on_cat_toggle(self, e):
        self.selected_cat = e.control.data if e.control.selected else None
        for chip in self.cat_row.controls:
            chip.selected = chip.data == self.selected_cat
        if self.cat_row.page:
            self.cat_row.update()
        self.selected_sub = None
        self.reload_sub_categories()
        self.apply_filters()

    def reload_sub_categories(self):
        self.sub_row.controls.clear()
        if self.selected_cat:
            sub_cats = self.raw_json.get(self.selected_cat, {}).keys()
            for sub in sub_cats:
                self.sub_row.controls.append(
                    ft.Chip(
                        label=ft.Text(sub, size=11, color="#FFFFFF"),
                        on_select=self.on_sub_toggle,
                        data=sub,
                        label_padding=ft.padding.symmetric(horizontal=4),
                        bgcolor=THEME_INNER_BG,
                        # 🛠️ FIX: Use 'border' here too
                        border_side=ft.BorderSide(width=0, color=ft.Colors.TRANSPARENT),
                        selected_color="#1B223D",
                    )
                )
        if self.sub_row.page:
            self.sub_row.update()

    def on_sub_toggle(self, e):
        self.selected_sub = e.control.data if e.control.selected else None
        for chip in self.sub_row.controls:
            chip.selected = chip.data == self.selected_sub
        if self.sub_row.page:
            self.sub_row.update()
        self.apply_filters()

    def on_tier_toggle(self, e):
        t = e.control.data
        if e.control.selected:
            self.selected_tiers.add(t)
        else:
            self.selected_tiers.discard(t)
        self.apply_filters()

    def on_enchant_toggle(self, e):
        en = e.control.data
        if e.control.selected:
            self.selected_enchants.add(en)
        else:
            self.selected_enchants.discard(en)
        self.apply_filters()

    def apply_filters(self):
        filtered = []
        search_term = self.search_input.value.lower() if self.search_input.value else ""

        for item in self.all_item_objects:
            if self.selected_cat and item.category != self.selected_cat:
                continue
            if self.selected_sub and item.sub_category != self.selected_sub:
                continue
            if self.selected_tiers and item.tier not in self.selected_tiers:
                continue
            if self.selected_enchants and item.enchant not in self.selected_enchants:
                continue
            if search_term and not (
                search_term in item.localized_name.lower()
                or search_term in item.unique_name.lower()
            ):
                continue

            filtered.append(item)

        self.left_panel.update_list(
            [i for i in filtered if i.unique_name not in self.preset_set]
        )
        self.right_panel.update_list(
            [i for i in filtered if i.unique_name in self.preset_set]
        )

    def add_single_item(self, item):
        self.preset_set.add(item.unique_name)
        self.apply_filters()

    def remove_single_item(self, item):
        self.preset_set.discard(item.unique_name)
        self.apply_filters()

    def add_items_bulk(self, items):
        for i in items:
            self.preset_set.add(i.unique_name)
        self.apply_filters()

    def remove_items_bulk(self, items):
        for i in items:
            self.preset_set.discard(i.unique_name)
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
            #self.settings.update_settings()

            show_popup(self.page, f"Preset '{name}.json' saved successfully!")
        except Exception as ex:
            show_popup(self.page, f"Error saving preset: {ex}", is_error=True)

    def delete_preset_click(self, e):
        fname = self.preset_dropdown.value
        if not fname:
            show_popup(self.page, "Please select a preset to delete.", is_error=True)
            return
        try:
            os.remove(os.path.join(PRESETS_DIR, fname))
            self.preset_dropdown.value = None
            self.update_preset_dropdown()
            self.settings.update_settings()
            show_popup(self.page, f"Preset '{fname}' deleted successfully!")
        except Exception as ex:
            show_popup(self.page, f"Error deleting preset: {ex}", is_error=True)
