import flet as ft

class GuiStyle:
    class Colors:
        WHITE = "#ffffff"
        LIGHT_GREEN = "#0d962b"
        GRAY_BLUE = "#1c2f4d"
        BLUE = "#1d4777"
        DARK_BLUE = "#0f1c31"

    class TextSize:
        SETTINGS_TITLE = 20

    SETTINGS_SAVE_BUTTON = ft.ButtonStyle(
        color=ft.Colors.WHITE,
        bgcolor=Colors.LIGHT_GREEN,
        shape=ft.RoundedRectangleBorder(radius=8),
        text_style=ft.TextStyle(
            size=TextSize.SETTINGS_TITLE,
            weight=ft.FontWeight.BOLD,
        ),
        alignment=ft.alignment.center,
    )

    SETTINGS_TOP_BAR_BUTTON = ft.ButtonStyle(
        color=ft.Colors.WHITE,
        bgcolor=ft.Colors.TRANSPARENT,
        shape=ft.RoundedRectangleBorder(radius=4),
        text_style=ft.TextStyle(
            size=TextSize.SETTINGS_TITLE,
            weight=ft.FontWeight.BOLD,
        ),
        elevation=0,
    )

    SETTINGS_TOP_BAR_BUTTON_SELECTED = ft.ButtonStyle(
        color=ft.Colors.WHITE,
        bgcolor=ft.Colors.TRANSPARENT,
        shape=ft.RoundedRectangleBorder(radius=4),
        text_style=ft.TextStyle(
            size=TextSize.SETTINGS_TITLE,
            weight=ft.FontWeight.BOLD,
        ),
        elevation=0,
    )
