import flet as ft

from .style import GuiStyle

def show_popup(page: ft.Page, message: str, is_error: bool = False):
    bg = GuiStyle.Colors.ACCENT_RED if is_error else GuiStyle.Colors.ACCENT_GREEN
    page.open(
        ft.SnackBar(
            ft.Text(message, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER),
            duration=1500,
            bgcolor=bg,
            dismiss_direction=ft.DismissDirection.UP,
        )
    )
