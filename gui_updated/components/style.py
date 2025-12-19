import flet as ft

class GuiStyle:
    class Colors:
        WHITE = "#ffffff"
        LIGHT_GREEN = "#0d962b"
        GRAY_BLUE = "#1c2f4d"

    SETTINGS_SAVE_BUTTON = ft.ButtonStyle(
        color=ft.Colors.WHITE,
        bgcolor=Colors.LIGHT_GREEN,
        shape=ft.RoundedRectangleBorder(radius=8),
    )

    SETTINGS_TOP_BAR_BUTTON = ft.ButtonStyle(
        color=ft.Colors.WHITE,
        shape=ft.RoundedRectangleBorder(radius=8),
    )
