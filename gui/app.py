import flet as ft
import threading
import asyncio

from gui import Header
from gui import Presets
from gui import BotOverlay
from gui import Dashboard
from gui import Settings
from gui.components.style import GuiStyle

from bot import Bot, SettingsHandler, LocalPlayer, Sniffer

class GuiApp:
    overlay: BotOverlay

    def __init__(self, page: ft.Page):
        self.main_column = None
        self.page = page
        self.page.title = "Market Trader - Local Version"
        self.page.window.icon = "app_icon.ico"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0
        self.page.bgcolor = GuiStyle.Colors.DARK_BLUE
        self.page.on_resized = self.on_page_resize
        self.page.fonts = {
            "Roboto Mono": "https://github.com/google/fonts/raw/main/apache/robotomono/RobotoMono-Regular.ttf"
        }

        # Initialize core bot components
        self.local_player = LocalPlayer()
        self.sniffer = Sniffer(self.local_player)
        sniffer_thread = threading.Thread(target=self.sniffer.start, daemon=True)
        sniffer_thread.start()

        self.config = SettingsHandler()
        self.overlay = BotOverlay()
        self.bot = Bot(self.sniffer, self.config, self.overlay, self.local_player)

        self.logger = self.bot.log_handler
        self.logger.start_session()
        self.logger.add_log("app", "Local Application started")

        # Initialize UI Components (Removed Login/Shop/Subscription)
        self.presets = self.config.get_presets_list()
        self.header = Header(page=self.page, on_nav_click=self.on_nav_click, settings=self.config)
        
        self.settings = Settings(page=self.page, config=self.config)
        self.presets = ft.Container(content=Presets(self.config, self.page, self.settings), padding=20)
        self.dashboard = Dashboard(app=self, config=self.config, page=self.page, bot=self.bot, header=self.header)

        self.body = ft.Container(content=self.dashboard, expand=True)
        self.main_column = ft.Column([self.header, self.body], expand=True, spacing=0)

        # Bypass login and go straight to the main app
        self.show_main_app()

    def show_main_app(self):
        self.page.controls.clear()
        self.page.add(self.main_column)
        try:
            self.page.update()
        except RuntimeError:
            pass

    def run_bot(self, task_name: str):
        if not self.bot:
            return
        task_to_run = getattr(self.bot, task_name, None)
        if callable(task_to_run):
            threading.Thread(
                target=self._run_async_task, 
                args=(task_to_run,), 
                daemon=True
            ).start()

    def _run_async_task(self, task_func):
        try:
            asyncio.run(task_func())
        except Exception as e:
            self.logger.add_log("error", f"Manual Task Error: {e}")

    def on_nav_click(self, event):
        for control in self.header.nav_rows.controls:
            control.style = ft.ButtonStyle(
                text_style=ft.TextStyle(color=GuiStyle.Colors.WHITE),
                color=GuiStyle.Colors.GREY_TEXT,
                bgcolor=GuiStyle.Colors.HEADER_BG,
                shape=ft.RoundedRectangleBorder(radius=8),
            )
        event.control.style = ft.ButtonStyle(
            text_style=ft.TextStyle(color=GuiStyle.Colors.WHITE),
            color=GuiStyle.Colors.WHITE,
            bgcolor=GuiStyle.Colors.HEADER_NAV_BUTTON_ACTIVE,
            shape=ft.RoundedRectangleBorder(radius=8),
            side={ft.ControlState.DEFAULT: ft.BorderSide(1, "#CDC7C7")},
        )

        if event.control.data == "settings":
            self.body.content = self.settings
        elif event.control.data == "presets":
            self.body.content = self.presets
        elif event.control.data == "dashboard":
            self.body.content = self.dashboard
        else:
            self.body.content = ft.Container(
                content=ft.Text(f"{event.control.text} View Placeholder", size=24, color=ft.Colors.GREY_500),
                alignment=ft.Alignment.CENTER, padding=50
            )
        try:
            self.page.update()
        except RuntimeError:
            pass

    def on_page_resize(self, e):
        try:
            self.page.update()
        except RuntimeError:
            pass

def main(page: ft.Page):
    app = GuiApp(page=page)
    page.window.prevent_close = True

    def on_window_event(e):
        if e.data == "close":
            if hasattr(app, 'overlay') and app.overlay:
                app.overlay.stop()
            if hasattr(app, 'logger'):
                app.logger.add_log("app", "Application closing")
                app.logger.end_session()
            page.window.destroy()

    page.window.on_event = on_window_event
    try:
        app.page.update()
    except RuntimeError:
        pass

if __name__ == "__main__":
    ft.run(main=main)