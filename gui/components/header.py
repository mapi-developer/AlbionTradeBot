import flet as ft
from typing import Callable
from .subscription import Subscription
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pages.login import Login
from bot import SettingsHandler
from gui.components.style import GuiStyle


def get_nav_button(title: str, data: str, icon: str, on_nav_click: Callable):
    button = ft.FilledTonalButton(
        text=title,
        icon=icon,
        on_click=on_nav_click,
        data=data,
        style=ft.ButtonStyle(
            text_style=ft.TextStyle(color=GuiStyle.Colors.TEXT_PRIMARY),
            color=GuiStyle.Colors.GREY_TEXT,
            bgcolor=GuiStyle.Colors.HEADER_BG,
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
    )
    if data == "dashboard":
        button.style.side = {
            ft.ControlState.DEFAULT: ft.BorderSide(1, GuiStyle.Colors.GREY_BORDER)
        }
        button.style.bgcolor = GuiStyle.Colors.HEADER_NAV_BUTTON_ACTIVE
        button.style.color = GuiStyle.Colors.TEXT_PRIMARY

    return button


class Header(ft.Container):
    def __init__(
        self,
        page: ft.Page,
        on_nav_click: Callable,
        login: Login,
        settings: SettingsHandler
    ):
        super().__init__()
        self.settings = settings
        self.login = login
        self.page = page
        self.bgcolor = GuiStyle.Colors.HEADER_BG
        self.margin = 0
        self.padding = 10

        self.nav_rows = ft.Row(
            controls=[
                get_nav_button("Dashboard", "dashboard", ft.Icons.HOME, on_nav_click),
                get_nav_button("Presets", "presets", ft.Icons.CREATE, on_nav_click),
                get_nav_button("Shop", "shop", ft.Icons.SHOP, on_nav_click),
                get_nav_button("Settings", "settings", ft.Icons.SETTINGS, on_nav_click),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        self.subscription = Subscription(self.page, login)

        self.logout_button = ft.FilledTonalButton(
            text="Logout",
            style=ft.ButtonStyle(
                text_style=ft.TextStyle(color=GuiStyle.Colors.GREY_TEXT),
                color=GuiStyle.Colors.GREY_TEXT,
                bgcolor=GuiStyle.Colors.HEADER_BG,
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=self.logout,
        )

        self.right_part = ft.Container(
            content=ft.Row(controls=[self.subscription, self.logout_button])
        )

        self.content = ft.Row(
            controls=[self.nav_rows, self.right_part],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    def logout(self, e):
        self.login.state.token = None
        self.login.state.user_id = None

        self.settings.set("auth_token", None)
        self.settings.set("user_id", None)

        self.page.controls.clear()
        self.page.add(self.login)

        if self.page:
            self.page.update()
