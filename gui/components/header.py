import os
import sys
from typing import Callable
import flet as ft

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import SettingsHandler
from gui.components.style import GuiStyle


def get_nav_button(title: str, data: str, icon: str, on_nav_click: Callable):
    button = ft.FilledTonalButton(
        content=ft.Text(title),
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
        settings: SettingsHandler,
    ):
        # Store settings reference
        self.settings = settings
        self.app_page = page  # Renamed from self.page to avoid Flet property conflict

        self.nav_rows = ft.Row(
            controls=[
                get_nav_button("Dashboard", "dashboard", ft.Icons.HOME, on_nav_click),
                get_nav_button("Presets", "presets", ft.Icons.CREATE, on_nav_click),
                get_nav_button("Settings", "settings", ft.Icons.SETTINGS, on_nav_click),
            ],
            alignment=ft.MainAxisAlignment.START,
        )

        # Pass layout attributes into super().__init__()
        super().__init__(
            bgcolor=GuiStyle.Colors.HEADER_BG,
            margin=0,
            padding=10,
            content=ft.Row(
                controls=[self.nav_rows],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
        )