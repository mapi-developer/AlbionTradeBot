import os
import sys
from typing import Callable
import flet as ft

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import SettingsHandler
from gui.components.style import GuiStyle
from pages.login import Login
from .popup import show_popup
from .subscription import Subscription


def get_nav_button(title: str, data: str, icon: str, on_nav_click: Callable):
    button = ft.FilledTonalButton(
        content=ft.Text(title),  # Replaced 'text' with 'content=ft.Text(...)'
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
        settings: SettingsHandler,
    ):
        # Store state attributes before building UI controls
        self.settings = settings
        self.login = login

        self.nav_rows = ft.Row(
            controls=[
                get_nav_button("Dashboard", "dashboard", ft.Icons.HOME, on_nav_click),
                get_nav_button("Presets", "presets", ft.Icons.CREATE, on_nav_click),
                get_nav_button("Shop", "shop", ft.Icons.SHOP, on_nav_click),
                get_nav_button("Settings", "settings", ft.Icons.SETTINGS, on_nav_click),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # Pass the 'page' argument directly rather than unattached 'self.page'
        self.subscription = Subscription(page, login)

        # --- User ID Component ---
        self.user_id_text = ft.Text(
            value="",
            color=GuiStyle.Colors.GREY_TEXT,
            size=12,
            weight=ft.FontWeight.NORMAL,
            font_family="Roboto Mono",  # Monospace looks better for IDs
        )

        self.user_id_container = ft.Container(
            content=self.user_id_text,
            padding=ft.Padding.only(left=10, right=10, top=5, bottom=5),  # Lowercase ft.padding
            border_radius=8,
            on_click=self.copy_user_id,
            tooltip="Click to copy User ID",
            ink=True,  # Ripple effect on click
            visible=False,  # Hidden until we have an ID
        )
        # -------------------------

        self.logout_button = ft.FilledTonalButton(
            content=ft.Text("Logout"),  # Replaced 'text' with 'content=ft.Text(...)'
            style=ft.ButtonStyle(
                text_style=ft.TextStyle(color=GuiStyle.Colors.GREY_TEXT),
                color=GuiStyle.Colors.GREY_TEXT,
                bgcolor=GuiStyle.Colors.HEADER_BG,
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=self.logout,
        )

        self.right_part = ft.Container(
            content=ft.Row(
                controls=[
                    self.subscription,
                    self.user_id_container,  # Added to the left of logout
                    self.logout_button,
                ],
                spacing=10,
            )
        )

        # Pass layout attributes into super().__init__() to comply with custom Control initialization
        super().__init__(
            bgcolor=GuiStyle.Colors.HEADER_BG,
            margin=0,
            padding=10,
            content=ft.Row(
                controls=[self.nav_rows, self.right_part],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
        )

    def copy_user_id(self, e):
        uid = self.login.state.user_id
        if uid:
            self.page.set_clipboard(uid)
            show_popup(self.page, f"Copied ID: {uid}")

    def update_user_id(self):
        """Fetches the user ID from login state and updates the display."""
        uid = self.login.state.user_id or self.settings.get("user_id")

        if uid:
            try:
                formatted_id = f"{int(uid):06d}"
            except (ValueError, TypeError):
                formatted_id = str(uid)

            self.user_id_text.value = f"ID: {formatted_id}"
            self.user_id_container.visible = True
        else:
            self.user_id_container.visible = False

        try:
            self.user_id_text.update()
            self.user_id_container.update()
        except RuntimeError:
            pass

    def logout(self, e):
        self.login.state.token = None
        self.login.state.user_id = None

        self.settings.set("auth_token", None)
        self.settings.set("user_id", None)

        self.page.controls.clear()
        self.page.add(self.login)

        try:
            self.page.update()
        except RuntimeError:
            pass