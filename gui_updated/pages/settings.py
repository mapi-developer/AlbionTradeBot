import flet as ft
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.style import GuiStyle

class UpperRow(ft.Container):
    def __init__(self):
        super().__init__()

        self.bgcolor = GuiStyle.Colors.GRAY_BLUE
        self.padding = 10
        self.margin = ft.margin.only(bottom=15)

        self.general_tab_button = ft.ElevatedButton(
            text="General",
            style=GuiStyle.SETTINGS_TOP_BAR_BUTTON,
        )
        self.fast_buy_tab_button = ft.ElevatedButton(
            text="Fast Buy",
            style=GuiStyle.SETTINGS_TOP_BAR_BUTTON,
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
                    controls= [
                        ft.Row(
                            controls=[
                                self.general_tab_button,
                                self.fast_buy_tab_button,
                                self.order_buy_tab_button
                            ]
                        )
                    ],
                    col={"md": 6},
                ),
                ft.Column(
                    controls=[self.save_button],
                    col={"md": 6},
                    horizontal_alignment=ft.CrossAxisAlignment.END,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )


class GeneralTab(ft.Container):
    def __init__(self):
        super().__init__()

        self.buy_mode = ft.Dropdown(
            label="Buy Mode Strategy",
            hint_text="Choose strategy for bot",
            value="",
            options=[
                ft.DropdownOption(text="Order Buy"),
                ft.DropdownOption(text="Fast Buy")
            ],
            dense=True,
            col={"md": 6}
        )

        self.content = ft.ResponsiveRow(
            controls=[
                self.buy_mode
            ]
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
                GeneralTab()
            ]
        )


def main(page: ft.Page):
    page.padding = 0
    app_settings = Settings(page=page)
    page.add(app_settings)
    page.update()

if __name__ == "__main__":
    ft.app(target=main)