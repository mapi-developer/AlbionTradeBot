import flet as ft
from typing import Callable
from .subscription import Subscription
from .login import Login

class Header(ft.Container):
    def __init__(self, page: ft.Page, on_nav_click: Callable, login: Login):
        super().__init__()
        self.page = page

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

        self.subscription = Subscription(self.page, login)

        self.content = ft.Row(
            controls=[self.nav_rows, self.subscription],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        self.bgcolor = "#15181F"
        self.padding = 10