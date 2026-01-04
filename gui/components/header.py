import flet as ft
from typing import Callable
from .subscription import Subscription
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pages.login import Login
from bot import SettingsManager
from gui.components.style import GuiStyle

class Header(ft.Container):
    def __init__(self, page: ft.Page, on_nav_click: Callable, login: Login, settings: SettingsManager = None):
        super().__init__()
        if settings == None: settings = SettingsManager()
        self.settings = settings
        self.login = login
        self.page = page
        self.margin = 0

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
                    "Shop",
                    icon=ft.Icons.SHOP,
                    on_click=on_nav_click,
                    data="shop",
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

        self.logout_button = ft.ElevatedButton(
            text="Logout",
            style=ft.ButtonStyle(
                text_style=ft.TextStyle(color="#C2C2C2"),
                color="#CDCDCD",
                bgcolor="#0A2449",
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=self.logout
        )

        self.right_part = ft.Container(
            content=ft.Row(
                controls=[
                    self.subscription,
                    self.logout_button
                ]
            )
        )

        self.content = ft.Row(
            controls=[self.nav_rows, self.right_part],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        self.bgcolor = "#15181F"
        self.padding = 10

    def logout(self, e):
        self.login.state.token = None
        self.login.state.user_id = None
        
        self.settings.set("auth_token", None)
        self.settings.set("user_id", None)
        
        self.page.controls.clear()
        self.page.add(self.login)

        if self.page:
            self.page.update()