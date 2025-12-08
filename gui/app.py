import flet as ft
import threading

from gui.components.header import Header
from gui.components.presets import Presets
from gui.components.settings import Settings
from gui.components.dashboard import Dashboard

from managers.config import ConfigManager
from database.interface import DatabaseInterface
from bot import TradeBot


class GuiApp:
    def __init__(self, page: ft.Page):
        self.main_column = None
        self.page = page
        self.page.title = "Albion Trade Bot"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0
        self.page.bgcolor = "#131415"
        self.page.on_resize = self.on_page_resize
        self.page.fonts = {
            "Roboto Mono": "https://github.com/google/fonts/raw/main/apache/robotomono/RobotoMono-Regular.ttf"
        }

        self.config = ConfigManager()
        self.bot = TradeBot(db=DatabaseInterface())

        self.presets = self.config.get_presets_list()
        self.header = Header(on_nav_click=self.on_nav_click)
        self.settings = Settings(self.config, self.page)
        self.presets = ft.Container(content=Presets(self.config, self.page))
        self.dashboard = ft.Container(
            content=Dashboard(self, self.config, self.page, self.bot),
            expand=True,
        )

        self.body = ft.Container(content=self.dashboard, expand=True)

        self.main_column = ft.Column([self.header, self.body], expand=True)
        self.page.add(self.main_column)

        self.page.update()

    def run_bot(self, task_name: str):
            if not self.bot:
                try:
                    print("Initializing bot...")
                    self.bot = TradeBot(db=DatabaseInterface())
                    print("Bot initialized.")
                except Exception as e:
                    print(f"Error initializing bot: {e}")
                    return

            if self.bot:
                task_to_run = getattr(self.bot, task_name, None)
                if callable(task_to_run):
                    threading.Thread(target=task_to_run, daemon=True).start()

    def on_nav_click(self, event):
        for control in self.header.nav_rows.controls:
            control.style = ft.ButtonStyle(
                text_style=ft.TextStyle(color="#FFFFFF"),
                color="#B8B7B7",
                bgcolor="#1C2F4D",
                shape=ft.RoundedRectangleBorder(radius=8),
            )
        event.control.style = ft.ButtonStyle(
            text_style=ft.TextStyle(color="#FFFFFF"),
            color="#FFFFFF",
            bgcolor="#0C2E5D",
            shape=ft.RoundedRectangleBorder(radius=8),
            side={ft.ControlState.DEFAULT: ft.BorderSide(1, "#CDC7C7")},
        )

        if event.control.data == "settings":
            self.settings.update_preset_dropdown()
            self.body.content = self.settings
        elif event.control.data == "presets":
            self.body.content = self.presets
        elif event.control.data == "dashboard":
            self.body.content = self.dashboard
        else:
            self.body.content = ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            f"{event.control.text} View Placeholder",
                            size=24,
                            color=ft.Colors.GREY_500,
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                alignment=ft.alignment.center,
                padding=50,
            )

        self.page.update()

    def on_page_resize(self, e):
        if self.main_column:
            self.main_column.update()


def main(page: ft.Page):
    app = GuiApp(page=page)
    app.page.update()


if __name__ == "__main__":
    ft.app(target=main)
