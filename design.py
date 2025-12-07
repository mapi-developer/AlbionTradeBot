import flet as ft
import threading
import re, os, json
from managers.config import ConfigManager, BUY_MODES, PRESETS_DIR, BOT_ITEMS_FILE
from database.interface import DatabaseInterface
from bot import TradeBot
from typing import Callable
from gui.modules.popup import show_popup


class ItemListPanel(ft.Container):
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
        self.bgcolor = "#1e293b"
        self.border_radius = 10
        self.border = ft.border.all(1, ft.Colors.GREY_800)
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
        self.count_text = ft.Text("0 items", size=11, color=ft.Colors.GREY_400)
        self.item_list = ft.ListView(
            expand=True, spacing=1, item_extent=35, auto_scroll=False
        )

        self.content = ft.Column(
            [
                ft.Text(title, weight=ft.FontWeight.BOLD, size=14),
                ft.Divider(height=5, thickness=1),
                ft.Row(
                    [self.action_btn, self.count_text],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(
                    content=self.item_list,
                    expand=True,
                    bgcolor="#162338",
                    border_radius=5,
                    padding=2,
                    height=420,
                ),  # 12 items * 35 extent
            ],
            spacing=5,
        )

    def update_list(self, items):
        self.current_items = items
        self.item_list.controls.clear()
        display_limit = 100
        for i, item in enumerate(items):
            if i >= display_limit:
                self.item_list.controls.append(
                    ft.Text(
                        f"... {len(items) - display_limit} more", size=11, italic=True
                    )
                )
                break
            self.item_list.controls.append(
                ft.ListTile(
                    leading=ft.Icon(self.item_icon, size=14, color=ft.Colors.GREY_400),
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
                                        ),
                                        ft.Text(
                                            item.unique_name,
                                            size=9,
                                            color=ft.Colors.GREY_500,
                                            font_family="Consolas",
                                            overflow=ft.TextOverflow.ELLIPSIS,
                                            no_wrap=True,
                                        ),
                                    ],
                                    spacing=2,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                                width=250,  # Set a fixed width for the text column
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
                    hover_color="#294E71",
                    on_click=lambda e, it=item: self.on_item_click(it),
                    content_padding=ft.padding.symmetric(vertical=0, horizontal=5),
                )
            )
        self.count_text.value = f"{len(items)} items"
        if self.item_list.page:
            self.item_list.update()
            self.count_text.update()

    def trigger_action(self, e):
        self.on_action_click(self.current_items)


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


class Header(ft.Container):
    def __init__(self, on_nav_click: Callable):
        super().__init__()

        self.nav_rows = ft.Row(
            controls=[
                ft.FilledTonalButton(
                    "Dashboard",
                    icon=ft.Icons.HOME,
                    on_click=on_nav_click,
                    data="dashboard",
                    style=ft.ButtonStyle(
                        text_style=ft.TextStyle(color="#FFFFFF"),
                        color="#FFFFFF",
                        bgcolor="#0C2E5D",
                        shape=ft.RoundedRectangleBorder(radius=8),
                        side={ft.ControlState.DEFAULT: ft.BorderSide(1, "#CDC7C7")},
                    ),
                ),
                ft.FilledTonalButton(
                    "Presets",
                    icon=ft.Icons.CREATE,
                    on_click=on_nav_click,
                    data="presets",
                    style=ft.ButtonStyle(
                        text_style=ft.TextStyle(color="#FFFFFF"),
                        color=ft.Colors.GREY_400,
                        bgcolor="#0C2E5D",
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                ),
                ft.FilledTonalButton(
                    "Settings",
                    icon=ft.Icons.SETTINGS,
                    on_click=on_nav_click,
                    data="settings",
                    style=ft.ButtonStyle(
                        text_style=ft.TextStyle(color="#FFFFFF"),
                        color=ft.Colors.GREY_400,
                        bgcolor="#0C2E5D",
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        self.user_info = ft.Row(
            controls=[
                ft.Column(
                    [
                        ft.Row(
                            controls=[
                                ft.Icon(
                                    name=ft.Icons.CIRCLE_ROUNDED,
                                    color="#089E28",
                                    size=10,
                                    offset=ft.Offset(0, 0.2),
                                ),
                                ft.Text(
                                    "active",
                                    style=ft.TextStyle(color="#089E28", size=12),
                                ),
                                ft.Text("Matvey4a", size=18),
                            ]
                        ),
                    ]
                ),
                ft.Column(
                    [
                        ft.CircleAvatar(
                            bgcolor=ft.Colors.BLUE_GREY_700,
                            radius=24,
                            foreground_image_src="https://render.albiononline.com/v1/item/UNIQUE_MOUNT_JUGGERNAUT_CRYSTAL",
                        )
                    ]
                ),
            ]
        )

        self.content = ft.Row(
            controls=[self.nav_rows, self.user_info],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        self.bgcolor = "#15181F"
        self.padding = 10


class Settings(ft.Container):
    def __init__(self, config: ConfigManager, page: ft.Page):
        super().__init__()
        self.padding = ft.padding.only(20, 10, 20, 0)
        self.config = config
        self.expand = True
        self.preset_options = []
        self.page = page
        self.update_preset_dropdown()

        self.save_button = ft.Container(
            ft.ElevatedButton(
                "Save Settings",
                icon=ft.Icons.SAVE,
                style=ft.ButtonStyle(
                    bgcolor="#148A23",
                    color="#ffffff",
                    shape=ft.RoundedRectangleBorder(radius=8),
                ),
                on_click=self.save_settings,
            ),
            alignment=ft.alignment.center_right,
            margin=ft.margin.only(0, 0, 25, 0),
        )

        self.general = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                "General Settings", weight=ft.FontWeight.BOLD, size=16
                            )
                        ]
                    ),
                    ft.Divider(color=ft.Colors.BLUE_GREY_800),
                    ft.Column(
                        [
                            ft.TextField(
                                label="Minimal Fast Profit Rate (%)",
                                value=int(
                                    self.config.get("general")["min_profit_rate_fast"]
                                    * 100
                                ),
                                data="min_profit_rate_fast",
                                suffix_text="%",
                                height=45,
                                text_size=14,
                                bgcolor="#0f172a",
                                border_color=ft.Colors.BLUE_GREY_700,
                                border_radius=8,
                                keyboard_type=ft.KeyboardType.NUMBER,
                            ),
                        ],
                        spacing=5,
                    ),
                    ft.Column(
                        [
                            ft.TextField(
                                label="Minimal Order Profit Rate (%)",
                                value=int(
                                    self.config.get("general")["min_profit_rate_order"]
                                    * 100
                                ),
                                data="min_profit_rate_order",
                                suffix_text="%",
                                height=45,
                                text_size=14,
                                bgcolor="#0f172a",
                                border_color=ft.Colors.BLUE_GREY_700,
                                border_radius=8,
                                keyboard_type=ft.KeyboardType.NUMBER,
                            ),
                        ],
                        spacing=5,
                    ),
                    ft.Column(
                        [
                            ft.TextField(
                                label="Default Buy Amount",
                                value=int(
                                    self.config.get("general")["default_buy_amount"]
                                ),
                                data="default_buy_amount",
                                suffix_text="items",
                                height=45,
                                text_size=14,
                                bgcolor="#0f172a",
                                border_color=ft.Colors.BLUE_GREY_700,
                                border_radius=8,
                                keyboard_type=ft.KeyboardType.NUMBER,
                            ),
                        ],
                        spacing=5,
                    ),
                    ft.Column(
                        [
                            ft.TextField(
                                label="Stop if Silver Lower Than",
                                value=int(self.config.get("general")["min_silver"]),
                                data="min_silver",
                                suffix_icon=ft.Icons.MONETIZATION_ON_OUTLINED,
                                height=45,
                                text_size=14,
                                bgcolor="#0f172a",
                                border_color=ft.Colors.BLUE_GREY_700,
                                border_radius=8,
                                keyboard_type=ft.KeyboardType.NUMBER,
                            ),
                        ],
                        spacing=5,
                    ),
                    ft.Column(
                        [
                            ft.Dropdown(
                                label="Buy Mode Strategy",
                                options=BUY_MODES,
                                data="buy_mode",
                                value=self.config.get("general")["buy_mode"],
                                text_size=14,
                                bgcolor="#0f172a",
                                border_color=ft.Colors.BLUE_GREY_700,
                                border_radius=8,
                            ),
                        ],
                        spacing=5,
                    ),
                ],
                spacing=15,
            ),
            bgcolor="#1e293b",
            padding=20,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.BLUE_GREY_700),
            col={"md": 3},
        )

        self.city_items = []
        for city in self.config.get("city_presets").keys():
            self.city_items.append(
                ft.Column(
                    [
                        ft.Dropdown(
                            label=" ".join(city.split("_")),
                            data=city,
                            options=self.preset_options,
                            value=self.config.get("city_presets")[city],
                            text_size=13,
                            content_padding=10,
                            bgcolor="#0f172a",
                            border_color=ft.Colors.BLUE_GREY_700,
                            border_radius=8,
                        ),
                    ],
                    spacing=5,
                )
            )

        city_panel = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("City Presets", weight=ft.FontWeight.BOLD, size=16),
                        ]
                    ),
                    ft.Divider(color=ft.Colors.BLUE_GREY_800),
                    ft.Column(self.city_items, spacing=15),
                ]
            ),
            bgcolor="#1e293b",
            padding=20,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.BLUE_GREY_700),
            col={"md": 3},
        )

        self.conditions_column = ft.Column(
            scroll=ft.ScrollMode.HIDDEN, spacing=5, expand=True, height=400
        )
        count_text = ft.Text("(0/20)", color=ft.Colors.GREY_500, size=12)
        add_btn = ft.ElevatedButton(
            "Add Condition",
            icon=ft.Icons.ADD,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.BLUE_GREY_700,
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )

        def update_condition_indices():
            for i, control in enumerate(self.conditions_column.controls):
                control.content.controls[0].content.value = f"#{i+1}"
                control.index = i + 1
            count_text.value = f"({len(self.conditions_column.controls)}/20)"

            if len(self.conditions_column.controls) >= 20:
                add_btn.disabled = True
                add_btn.bgcolor = ft.Colors.BLUE_GREY_900
            else:
                add_btn.disabled = False
                add_btn.bgcolor = ft.Colors.BLUE_GREY_700

            if self.conditions_column.page:
                page.update()

        def remove_condition(row_instance):
            self.conditions_column.controls.remove(row_instance)
            update_condition_indices()

        def add_condition_click(e, values=None):
            if len(self.conditions_column.controls) >= 20:
                return

            new_index = len(self.conditions_column.controls) + 1
            row = self.ConditionRow(new_index, remove_condition)
            self.conditions_column.controls.append(row)

            if self.conditions_column.page:
                self.conditions_column.scroll_to(offset=-1, duration=300)

            if values != None:
                row.content.controls[2].content.value = values[0]
                row.content.controls[4].content.value = values[1]

            update_condition_indices()

        for _, condition in enumerate(self.config.get("buy_logic")):
            add_condition_click(
                0, [condition["amount_to_buy"], condition["price_larger_then"]]
            )

        add_btn.on_click = add_condition_click

        logic_panel = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        "Buy Logic", weight=ft.FontWeight.BOLD, size=16
                                    ),
                                    count_text,
                                ]
                            ),
                            add_btn,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(color=ft.Colors.BLUE_GREY_800),
                    ft.Container(
                        content=self.conditions_column,
                        bgcolor="#0f172a",  # Darker bg for the list area
                        border_radius=8,
                        border=ft.border.all(1, ft.Colors.BLUE_GREY_800),
                        padding=8,
                    ),
                    ft.Container(
                        ft.Text(
                            "* Logic is evaluated top to bottom. If no match, Default Amount is used.",
                            italic=True,
                            size=12,
                            color=ft.Colors.GREY_500,
                        ),
                        margin=ft.margin.only(0, 10, 0, 0),
                    ),
                ],
                spacing=5,
            ),
            bgcolor="#1e293b",
            padding=20,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.BLUE_GREY_700),
            expand=True,
            col={"md": 6},  # 50% width
        )

        settings_row_content = ft.ResponsiveRow(
            [self.general, city_panel, logic_panel], spacing=20
        )

        self.scrollable_content = ft.Column(
            controls=[self.save_button, settings_row_content],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=20,
        )

        self.content = self.scrollable_content

    def save_settings(self, e):
        settings_to_save = {
            "general": {
                "min_profit_rate_fast": float(
                    self.general.content.controls[2].controls[0].value
                )
                / 100,
                "min_profit_rate_order": float(
                    self.general.content.controls[3].controls[0].value
                )
                / 100,
                "default_buy_amount": int(
                    self.general.content.controls[4].controls[0].value
                ),
                "min_silver": int(self.general.content.controls[5].controls[0].value),
                "buy_mode": self.general.content.controls[6].controls[0].value,
            },
            "city_presets": {
                "fort_sterling": self.city_items[0].controls[0].value,
                "lymhurst": self.city_items[1].controls[0].value,
                "bridgewatch": self.city_items[2].controls[0].value,
                "martlock": self.city_items[3].controls[0].value,
                "thetford": self.city_items[4].controls[0].value,
                "caerleon": self.city_items[5].controls[0].value,
                "brecilien": self.city_items[6].controls[0].value,
            },
            "buy_logic": [],
        }

        for _, control in enumerate(self.conditions_column.controls):
            settings_to_save["buy_logic"].append(
                {
                    "amount_to_buy": control.content.controls[2].content.value,
                    "price_larger_then": control.content.controls[4].content.value,
                }
            )

        self.config.save_settings(settings_to_save)
        show_popup(self.page, "Settings Saved Successfully!")

    def update_preset_dropdown(self):
        files = self.config.get_presets_list()
        self.preset_options = []
        for f in files:
            self.preset_options.append(ft.dropdown.Option(f))
        if self.page:
            self.page.update()

    class ConditionRow(ft.Container):
        def __init__(self, index, remove_callback):
            super().__init__()
            self.index = index
            self.remove_callback = remove_callback
            self.padding = ft.padding.only(10, 0, 0, 0)
            self.bgcolor = "#182F4A"
            self.border_radius = 8
            self.border = ft.border.all(1, ft.Colors.BLUE_GREY_800)
            self.expand = True

            self.amount_field = ft.TextField(
                value="0",
                text_size=13,
                content_padding=2,
                text_align=ft.TextAlign.CENTER,
                border_color=ft.Colors.BLUE_GREY_700,
                keyboard_type=ft.KeyboardType.NUMBER,
            )

            self.price_field = ft.TextField(
                value="0",
                text_size=13,
                content_padding=10,
                text_align=ft.TextAlign.CENTER,
                border_color=ft.Colors.BLUE_GREY_700,
                keyboard_type=ft.KeyboardType.NUMBER,
            )

            self.content = ft.ResponsiveRow(
                controls=[
                    ft.Container(
                        content=ft.Text(f"#{index}", color=ft.Colors.GREY_500, size=12),
                        col={"md": 1},
                    ),
                    ft.Container(
                        content=ft.Text(
                            "Buy",
                            color=ft.Colors.GREY_400,
                            size=13,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        col={"md": 1},
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(content=self.amount_field, col={"md": 2}),
                    ft.Container(
                        content=ft.Text(
                            "items if price >", color=ft.Colors.GREY_400, size=13
                        ),
                        col={"md": 3},
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(content=self.price_field, col={"md": 2}),
                    ft.Container(
                        content=ft.Text("silver", color=ft.Colors.GREY_400, size=12),
                        col={"md": 1},
                        alignment=ft.alignment.center,
                    ),
                    self.MyDeleteButton(remove_callback, self),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )

        class MyDeleteButton(ft.Container):
            def __init__(self, remove_callback, condition_row):
                super().__init__(
                    width=36,
                    height=36,
                    alignment=ft.alignment.center,
                    foreground_decoration=ft.BoxDecoration(
                        shape=ft.BoxShape.CIRCLE,
                        bgcolor=ft.Colors.TRANSPARENT,
                    ),
                    content=ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_color=ft.Colors.GREY_500,
                        icon_size=20,
                        tooltip="Remove Condition",
                        on_click=lambda e: remove_callback(condition_row),
                    ),
                    on_hover=self._on_hover,
                    col={"md": 2},
                )

            def _on_hover(self, e: ft.HoverEvent):
                if e.data == "true":
                    self.content.icon_color = ft.Colors.RED_900
                else:
                    self.content.icon_color = ft.Colors.GREY_500

                e.control.update()


class Presets(ft.Column):
    def __init__(self, config: ConfigManager, page: ft.Page):
        super().__init__()
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
            bgcolor="#22374F",
            border_color="#233448",
        )

        def create_chip(text, data, callback):
            return ft.Chip(
                label=ft.Text(text, size=11, color="#FFFFFF"),
                on_select=callback,
                data=data,
                label_padding=ft.padding.symmetric(horizontal=4),
                bgcolor="#133153",
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
            border_color=ft.Colors.GREY_800,
        )
        self.update_preset_dropdown()

        self.filename_input = ft.TextField(
            label="Save as",
            suffix_text=".json",
            text_size=12,
            expand=True,
            dense=True,
            height=35,
            bgcolor="#22374F",
            border_color="#233448",
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
            bgcolor="#1e293b",
            border_radius=5,
            border=ft.border.all(1, ft.Colors.GREY_800),
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
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_FOREVER,
                            on_click=self.delete_preset_click,
                            icon_color=ft.Colors.RED_400,
                            tooltip="Delete",
                        ),
                        ft.VerticalDivider(width=10, color=ft.Colors.GREY_700),
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
                bgcolor="#1e293b",
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
                bgcolor="#133153",
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
                        bgcolor="#133153",
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
            #
            show_popup(self.page, f"Preset '{name}.json' saved successfully!")
        except Exception as ex:
            show_popup(self.page, f"Error saving preset: {ex}", is_error=True)

    def delete_preset_click(self, e):
        fname = self.preset_dropdown.value
        if not fname:
            return
        try:
            os.remove(os.path.join(PRESETS_DIR, fname))
            self.update_preset_dropdown()
            self.preset_dropdown.value = None
            if self.preset_dropdown.page:
                self.preset_dropdown.update()
        except:
            pass


class Dashboard(ft.Column):
    def __init__(self, config: ConfigManager, page: ft.Page, bot: TradeBot):
        super().__init__()
        self.config = config
        self.page = page
        self.bot = bot
        self.expand=True

        def on_tab_change(event):
            if event.control.data == "home":
                self.controls = [ft.ResponsiveRow(controls=[self.left_panel, self.home_page_tab], expand=True)]
            elif event.control.data == "commands":
                self.controls = [ft.ResponsiveRow(controls=[self.left_panel, self.bot_commands_tab], expand=True)]
            elif event.control.data == "activity":
                self.controls = [ft.ResponsiveRow(controls=[self.left_panel, self.activity_log_tab], expand=True)]
            else:
                print(f"No Tab found: {event.control.data}")

            self.update()

        self.page.update()

        self.left_panel_upper_buttons = ft.Column(
            controls=[
                ft.Container(
                    content=ft.ElevatedButton(
                        text="Home Page",
                        data="home",
                        on_click=on_tab_change,
                        style=ft.ButtonStyle(
                            color="#ffffff",
                            shape=ft.RoundedRectangleBorder(radius=0),
                            bgcolor="#294D7C"
                        )
                    ),
                ),
                ft.Container(
                    content=ft.ElevatedButton(
                        text="Bot Commands",
                        data="commands",
                        on_click=on_tab_change,
                        style=ft.ButtonStyle(
                            color="#ffffff",
                            shape=ft.RoundedRectangleBorder(radius=0),
                            bgcolor="#294D7C"
                        )
                    ),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            spacing=0
        )

        self.info_button = ft.Column(
            controls=[
                ft.Container(
                    content=ft.ElevatedButton(
                        text="Activity Log",
                        data="activity",
                        on_click=on_tab_change,
                        icon=ft.Icons.INFO_OUTLINE,
                        style=ft.ButtonStyle(
                            color="#ffffff",
                            shape=ft.RoundedRectangleBorder(radius=0),
                            bgcolor="#294D7C"
                        )
                    ),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            spacing=0
        )

        self.left_panel_content = ft.Column(
            controls=[
                self.left_panel_upper_buttons, 
                self.info_button
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        self.left_panel = ft.Container(
            content=self.left_panel_content,
            bgcolor="#294D7C",
            col={"md": 2},
            expand=True
        )

        self.bot_buttons = ft.Column(
            controls=[ft.Row(
                controls=[
                    ft.OutlinedButton(
                        "Check Prices",
                        style=ft.ButtonStyle(
                            color=ft.Colors.WHITE, 
                            bgcolor="#91640A",
                            shape=ft.RoundedRectangleBorder(radius=8),
                            side=ft.BorderSide(1, "#CB9935")
                        ),
                    ),
                    ft.OutlinedButton(
                        "Buy Items",
                        style=ft.ButtonStyle(
                            color=ft.Colors.WHITE, 
                            bgcolor="#75179A",
                            shape=ft.RoundedRectangleBorder(radius=8),
                            side=ft.BorderSide(1, "#9A26AE")
                        ),
                    ),
                ]
            )]
        )

        self.overview_row = ft.Row(
            controls=[
                ft.Text(
                    "Trade Bot overview:",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                )
            ]
        )

        self.home_page_tab = ft.Container(
            content=ft.Column(controls=[self.overview_row]),
            expand=True,
            col={"md": 10},
        )

        self.bot_commands_tab = ft.Container(
            content=self.bot_buttons,
            expand=True,
            col={"md": 10}
        )

        self.activity_log_tab = ft.Container(
            content=ft.Text("Activity Log"),
            expand=True,
            col={"md": 10}
        )

        self.controls = [ft.ResponsiveRow(controls=[self.left_panel, self.home_page_tab], expand=True)]


class GuiApp:
    def __init__(self, page: ft.Page):
        self.main_column = None
        self.page = page
        self.page.title = "Albion Trade Bot"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0
        self.page.bgcolor = "#131415"
        self.page.on_resize = self.on_page_resize
        self.page.fonts = {
            "Roboto Mono": "https://github.com/google/fonts/raw/main/apache/robotomono/RobotoMono-Regular.ttf"
        }

        self.config = ConfigManager()
        self.bot = None

        def run_bot(task_name: str):
            if not self.bot:
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

        self.presets = self.config.get_presets_list()
        self.header = Header(on_nav_click=self.on_nav_click)
        self.settings = Settings(self.config, self.page)
        self.presets = ft.Container(content=Presets(self.config, self.page))
        self.dashboard = ft.Container(
            content=Dashboard(self.config, self.page, self.bot),
            expand=True,
        )

        self.body = ft.Container(content=self.dashboard, expand=True)

        self.main_column = ft.Column([self.header, self.body], expand=True)
        self.page.add(self.main_column)

        self.page.update()

    def on_nav_click(self, event):
        for control in self.header.nav_rows.controls:
            control.style = ft.ButtonStyle(
                text_style=ft.TextStyle(color="#FFFFFF"),
                color="#B8B7B7",
                bgcolor="#1C2F4D",
                shape=ft.RoundedRectangleBorder(radius=8),
            )
        event.control.style = ft.ButtonStyle(
            text_style=ft.TextStyle(color="#FFFFFF"),
            color="#FFFFFF",
            bgcolor="#0C2E5D",
            shape=ft.RoundedRectangleBorder(radius=8),
            side={ft.ControlState.DEFAULT: ft.BorderSide(1, "#CDC7C7")},
        )

        if event.control.data == "settings":
            self.body.content = self.settings
        elif event.control.data == "presets":
            self.body.content = self.presets
        elif event.control.data == "dashboard":
            self.body.content = self.dashboard
        else:
            self.body.content = ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            f"{event.control.text} View Placeholder",
                            size=24,
                            color=ft.Colors.GREY_500,
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                alignment=ft.alignment.center,
                padding=50,
            )

        self.page.update()

    def on_page_resize(self, e):
        if self.main_column:
            self.main_column.update()


def main(page: ft.Page):
    app = GuiApp(page=page)

    app.page.update()


if __name__ == "__main__":
    ft.app(target=main)
