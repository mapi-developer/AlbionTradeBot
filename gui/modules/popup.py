# gui/popup.py
import flet as ft

def show_popup(page: ft.Page, message: str, is_error: bool = False):
    bg = ft.Colors.RED if is_error else ft.Colors.GREEN
    page.open(ft.SnackBar(ft.Text(message, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER), duration=1500, bgcolor=bg, dismiss_direction=ft.DismissDirection.UP))