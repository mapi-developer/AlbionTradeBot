import flet as ft
from typing import Callable

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