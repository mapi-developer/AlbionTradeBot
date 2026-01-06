import flet as ft
import threading

from gui import Header
from gui import Presets
from gui import Login
from gui import Subscription
from gui import BotOverlay
from gui import Dashboard
from gui import Settings
from gui import Shop
from gui.components.style import GuiStyle

from bot import Bot, SettingsManager, Logger, AlbionSniffer

class GuiApp:
    overlay:BotOverlay

    def __init__(self, page: ft.Page):
        self.main_column = None
        self.page = page
        self.page.title = "Market Trader"
        self.page.window.icon = "app_icon.ico"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0
        self.page.bgcolor = GuiStyle.Colors.DARK_BLUE
        self.page.on_resized = self.on_page_resize
        self.page.fonts = {
            "Roboto Mono": "https://github.com/google/fonts/raw/main/apache/robotomono/RobotoMono-Regular.ttf"
        }

        self.config = SettingsManager()

        self.logger = Logger()
        self.logger.start_session()
        self.logger.add_log("app", "Application started")

        self.login = Login(self.page, on_login_success=self.show_main_app, settings=self.config)

        self.bot = Bot(logger=self.logger)
        self.overlay = BotOverlay()

        self.presets = self.config.get_presets_list()
        self.header = Header(page = self.page, on_nav_click=self.on_nav_click, login=self.login, settings=self.config)
        
        # Initialize views
        self.settings = Settings(page=self.page, config=self.config)
        self.presets = ft.Container(content=Presets(self.config, self.page, self.settings))
        self.dashboard = Dashboard(app=self, config=self.config, page=self.page, bot=self.bot, header=self.header, logger=self.logger, login=self.login)

        self.shop = Shop(settings=self.config, login_state=self.login.state)
        
        # Pass the Header's subscription widget to the Tab so it can update status after purchase
        self.subscription_tab = Subscription(
            self.page, 
            self.login
        )

        self.header.subscription.open_subscriptions_offer.on_click = lambda e: self.go_to_subscription()

        self.body = ft.Container(content=self.dashboard, expand=True)

        self.main_column = ft.Column([self.header, self.body], expand=True, spacing=0)
        saved_token = self.config.get("auth_token")
        saved_user_id = self.config.get("user_id")

        if saved_token and saved_user_id:
            print("Auto-login found. Skipping login screen.")
            self.login.state.token = saved_token
            self.login.state.user_id = saved_user_id
            
            # Show the main app directly
            self.show_main_app()
        else:
            # No token found, show login screen
            if self.page:
                self.page.add(self.login)

        if self.page:
            self.page.update()

    def show_main_app(self):
        self.header.subscription.check_subscription()
        self.page.controls.clear()
        self.page.add(self.main_column)
        if self.page:
            self.page.update()
        #self.dashboard.update_overview()

    def run_bot(self, task_name: str):
            if self.bot: self.bot.destroy()
            if not self.bot:
                try:
                    self.bot = Bot(logger=self.logger)
                except Exception as e:
                    self.logger.add_log("error", f"Bot initialization failed: {e}")
                    return

            if self.bot:
                task_to_run = getattr(self.bot, task_name, None)
                if callable(task_to_run):
                    threading.Thread(target=task_to_run, daemon=True).start()

    def go_to_subscription(self):
        for control in self.header.nav_rows.controls:
            control.style = ft.ButtonStyle(
                text_style=ft.TextStyle(color=GuiStyle.Colors.WHITE),
                color=GuiStyle.Colors.GREY_TEXT,
                bgcolor=GuiStyle.Colors.HEADER_BG,
                shape=ft.RoundedRectangleBorder(radius=8),
            )
        self.header.nav_rows.controls[2].style = ft.ButtonStyle(
            text_style=ft.TextStyle(color=GuiStyle.Colors.WHITE),
            color=GuiStyle.Colors.WHITE,
            bgcolor=GuiStyle.Colors.HEADER_NAV_BUTTON_ACTIVE,
            shape=ft.RoundedRectangleBorder(radius=8),
            side={ft.ControlState.DEFAULT: ft.BorderSide(1, "#CDC7C7")},
        )
        self.body.content = self.shop
        if self.page:
            self.page.update()

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
        elif event.control.data == "shop":
            self.body.content = self.shop
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

        if self.page:
            self.page.update()

    def on_page_resize(self, e):
        if self.main_column.page:
            self.main_column.page.update()


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
    app.page.update()


if __name__ == "__main__":
    ft.app(target=main)