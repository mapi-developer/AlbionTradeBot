import flet as ft
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from components.style import GuiStyle
from managers.config import AVALIABLE_LANGUAGES

class UpperRow(ft.Container):
    def __init__(self):
        super().__init__()

        self.bgcolor = GuiStyle.Colors.GRAY_BLUE
        self.padding = 10

        general_title = ft.Text(
            value="General",
            style=ft.TextStyle(
                size=GuiStyle.TextSize.SETTINGS_TITLE,
                color=ft.Colors.WHITE,
                weight=ft.FontWeight.BOLD,
            )
        )
        general_title_row = ft.Container(
            padding=ft.padding.only(10, 0, 10, 0),
            content=general_title
        )

        self.fast_buy_tab_button = ft.ElevatedButton(
            text="Fast Buy",
            style=GuiStyle.SETTINGS_TOP_BAR_BUTTON_SELECTED,
        )
        self.order_buy_tab_button = ft.ElevatedButton(
            text="Order Buy",
            style=GuiStyle.SETTINGS_TOP_BAR_BUTTON,
        )

        self.save_button = ft.ElevatedButton(
            icon=ft.Icons.SAVE,
            text="Save Settings",
            style=GuiStyle.SETTINGS_SAVE_BUTTON,
        )

        self.content = ft.ResponsiveRow(
            controls=[
                ft.Column(
                    controls=[
                        general_title_row
                    ],
                    col={"sm": 0, "md": 6, "xl": 4},
                ),
                ft.Column(
                    controls= [
                        ft.Row(
                            controls=[
                                self.fast_buy_tab_button,
                                self.order_buy_tab_button,
                            ]
                        )
                    ],
                    col={"sm": 6, "md": 3, "xl": 4},
                ),
                ft.Column(
                    controls=[self.save_button],
                    col={"sm": 6, "md": 3, "xl": 4},
                    horizontal_alignment=ft.CrossAxisAlignment.END,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )


class SettingsDropdown(ft.Dropdown):
    def __init__(self, label: str, tooltip: str, options: list[ft.DropdownOption]):
        super().__init__(
            label = label,
            tooltip = tooltip,
            options = options,
            dense=True,
            expand=True,
            col={"sm": 12, "md": 6, "xl": 4},
            filled=True,
            fill_color=GuiStyle.Colors.GRAY_BLUE,
            color=ft.Colors.WHITE,
            text_style=ft.TextStyle(color=ft.Colors.WHITE),
            label_style=ft.TextStyle(color=ft.Colors.WHITE)
        )


class GeneralSettings(ft.Container):
    def __init__(self):
        super().__init__()
        self.padding = 20
        self.col={"sm": 12, "md": 6, "xl": 4}

        self.buy_mode = SettingsDropdown(
            label="Buy Mode Strategy", 
            tooltip="Choose strategy for bot",
            options=[
                ft.DropdownOption(text="Order Buy"),
                ft.DropdownOption(text="Fast Buy")
            ]  
        )

        self.game_language = SettingsDropdown(
            label="Language in Game",
            tooltip="Choose your in game Language",
            options = [ft.DropdownOption(key=language, text=language) for language in AVALIABLE_LANGUAGES],
        )

        self.stop_silver_threshold = ft.TextField(
            label="Stop if Silver lower Than",
            tooltip="Bot will stop if your silver will be lower",
            border_color=GuiStyle.Colors.GRAY_BLUE,
            color=ft.Colors.WHITE,
            label_style=ft.TextStyle(color=ft.Colors.WHITE),
            fill_color=GuiStyle.Colors.DARK_BLUE,
        )

        self.content = ft.ResponsiveRow(
            controls=[
                ft.Column(
                    controls = [
                        self.buy_mode,
                        self.game_language,
                        self.stop_silver_threshold,
                    ],
                    col=12,
                )
            ],
        )


class FastBuySettings(ft.Container):
    # Default buy amount
    # City presets
    # Buy logic
    def __init__(self):
        super().__init__()
        self.bgcolor = "#2D4F78"
        self.padding = 20
        self.col={"sm": 12, "md": 6, "xl": 8}

        self.minimal_profit_rate = ft.TextField(
            label="Minimal Profit Rate",
            fill_color=GuiStyle.Colors.DARK_BLUE,
        )

        self.content = ft.ResponsiveRow(
            controls=[
                ft.Column(
                    controls = [
                        self.minimal_profit_rate
                    ],
                    col={"sm": 12, "md": 8, "xl": 4},
                )
            ],
        )

class SettingsMain(ft.Container):
    def __init__(self):
        super().__init__()

        self.content = ft.ResponsiveRow(
            controls=[
                GeneralSettings(),
                FastBuySettings(),     
            ],
            spacing=20,
            run_spacing=20,
        )


class Settings(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.margin = 0
        self.padding = 0
        self.page = page
        self.content = ft.Column(
            controls=[
                UpperRow(),
                SettingsMain()
            ],
            spacing = 0,
        )


def main(page: ft.Page):
    page.padding = 0
    app_settings = Settings(page=page)
    page.add(app_settings)
    page.update()

if __name__ == "__main__":
    ft.app(target=main)