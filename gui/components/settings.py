import flet as ft
from managers.config import ConfigManager, BUY_MODES
from .popup import show_popup


THEME_PANEL_BG = "#294D7C"  # Main container color
THEME_INNER_BG = "#203064"  # Inner cards/inputs color
THEME_BORDER_C = ft.Colors.with_opacity(0.1, ft.Colors.WHITE)


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
                    ft.Divider(color=ft.Colors.WHITE24),
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
                                bgcolor=THEME_INNER_BG,
                                border_color=ft.Colors.TRANSPARENT,
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
                                bgcolor=THEME_INNER_BG,
                                border_color=ft.Colors.TRANSPARENT,
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
                                bgcolor=THEME_INNER_BG,
                                border_color=ft.Colors.TRANSPARENT,
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
                                bgcolor=THEME_INNER_BG,
                                border_color=ft.Colors.TRANSPARENT,
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
                                bgcolor=THEME_INNER_BG,
                                border_color=ft.Colors.TRANSPARENT,
                                border_radius=8,
                                fill_color=THEME_INNER_BG,
                                filled=True,
                            ),
                        ],
                        spacing=5,
                    ),
                ],
                spacing=15,
            ),
            bgcolor=THEME_PANEL_BG,
            padding=20,
            border_radius=12,
            border=ft.border.all(1, THEME_BORDER_C),
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
                            bgcolor=THEME_INNER_BG,
                            border_color=ft.Colors.TRANSPARENT,
                            border_radius=8,
                            fill_color=THEME_INNER_BG,
                            filled=True,
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
                    ft.Divider(color=ft.Colors.WHITE24),
                    ft.Column(self.city_items, spacing=15),
                ]
            ),
            bgcolor=THEME_PANEL_BG,
            padding=20,
            border_radius=12,
            border=ft.border.all(1, THEME_BORDER_C),
            col={"md": 3},
        )

        self.conditions_column = ft.Column(
            scroll=ft.ScrollMode.HIDDEN, spacing=5, expand=True, height=400
        )
        count_text = ft.Text("(0/20)", color=ft.Colors.WHITE54, size=12)
        add_btn = ft.ElevatedButton(
            "Add Condition",
            icon=ft.Icons.ADD,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=THEME_INNER_BG,
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
                add_btn.bgcolor = THEME_INNER_BG

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
                    ft.Divider(color=ft.Colors.WHITE24),
                    ft.Container(
                        content=self.conditions_column,
                        bgcolor=THEME_INNER_BG,
                        border_radius=8,
                        padding=8,
                    ),
                    ft.Container(
                        ft.Text(
                            "* Logic is evaluated top to bottom. If no match, Default Amount is used.",
                            italic=True,
                            size=12,
                            color=ft.Colors.WHITE54,
                        ),
                        margin=ft.margin.only(0, 10, 0, 0),
                    ),
                ],
                spacing=5,
            ),
            bgcolor=THEME_PANEL_BG,
            padding=20,
            border_radius=12,
            border=ft.border.all(1, THEME_BORDER_C),
            expand=True,
            col={"md": 6},
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

    def update_settings(self):
        self.update_preset_dropdown()
        for item in self.city_items:
            dropdown = item.controls[0]
            dropdown.options = self.preset_options
        if self.page:
            self.page.update()

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
            self.bgcolor = THEME_PANEL_BG
            self.border_radius = 8
            self.border = ft.border.all(1, THEME_BORDER_C)
            self.expand = True

            self.amount_field = ft.TextField(
                value="0",
                text_size=13,
                content_padding=2,
                text_align=ft.TextAlign.CENTER,
                border_color=ft.Colors.TRANSPARENT,
                bgcolor=THEME_INNER_BG,
                keyboard_type=ft.KeyboardType.NUMBER,
            )

            self.price_field = ft.TextField(
                value="0",
                text_size=13,
                content_padding=10,
                text_align=ft.TextAlign.CENTER,
                border_color=ft.Colors.TRANSPARENT,
                bgcolor=THEME_INNER_BG,
                keyboard_type=ft.KeyboardType.NUMBER,
            )

            self.content = ft.ResponsiveRow(
                controls=[
                    ft.Container(
                        content=ft.Text(f"#{index}", color=ft.Colors.WHITE54, size=12),
                        col={"md": 1},
                    ),
                    ft.Container(
                        content=ft.Text(
                            "Buy",
                            color=ft.Colors.WHITE70,
                            size=13,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        col={"md": 1},
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(content=self.amount_field, col={"md": 2}),
                    ft.Container(
                        content=ft.Text(
                            "items if price >", color=ft.Colors.WHITE70, size=13
                        ),
                        col={"md": 3},
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(content=self.price_field, col={"md": 2}),
                    ft.Container(
                        content=ft.Text("silver", color=ft.Colors.WHITE70, size=12),
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
                        icon_color=ft.Colors.WHITE54,
                        icon_size=20,
                        tooltip="Remove Condition",
                        on_click=lambda e: remove_callback(condition_row),
                    ),
                    on_hover=self._on_hover,
                    col={"md": 2},
                )

            def _on_hover(self, e: ft.HoverEvent):
                if e.data == "true":
                    self.content.icon_color = ft.Colors.RED_ACCENT
                else:
                    self.content.icon_color = ft.Colors.WHITE54

                e.control.update()