import flet as ft
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.style import GuiStyle

class UpperRow(ft.ResponsiveRow):
    def __init__(self):
        super().__init__()
        self.fast_buy_button = ft.ElevatedButton(
            text="Fast Buy",
            style=GuiStyle.SETTINGS_TOP_BAR_BUTTON,
        )
        self.order_buy_button = ft.ElevatedButton(
            text="Order Buy",
            style=GuiStyle.SETTINGS_TOP_BAR_BUTTON,
        )

        self.save_button = ft.ElevatedButton(
            icon=ft.Icons.SAVE,
            text="Save Settings",
            style=GuiStyle.SETTINGS_SAVE_BUTTON,
        )

        self.controls = [  
            ft.Column(
                controls= [
                    ft.Row(
                        controls=[
                            self.fast_buy_button,
                            self.order_buy_button
                        ]
                    )
                ],
                col={"md": 8},
            ),
            ft.Column(
                controls=[self.save_button],
                col={"md": 4},
                horizontal_alignment=ft.CrossAxisAlignment.END,
            ),
        ]
        

class Settings(ft.Container):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.content = ft.Column(
            controls=[
                UpperRow()
            ]
        )


def main(page: ft.Page):
    app_settings = Settings(page=page)
    page.add(app_settings)
    page.update()

if __name__ == "__main__":
    ft.app(target=main)