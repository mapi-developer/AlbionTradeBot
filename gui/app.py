import flet as ft
import threading

from gui.components import Header
from gui.pages import Presets
from gui.pages import Login
from gui.components import SubscriptionTab
from gui.components import BotOverlay
from gui.pages import Dashboard
from gui.pages import Settings
from gui.pages import Shop

from managers.config import ConfigManager
from database.interface import DatabaseInterface
from bot import TradeBot


class GuiApp:
    overlay:BotOverlay

    def __init__(self, page: ft.Page):
        self.main_column = None
        self.page = page
        self.page.title = "Albion Trade Bot"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0
        self.page.bgcolor = "#131415"
        self.page.on_resized = self.on_page_resize
        self.page.fonts = {
            "Roboto Mono": "https://github.com/google/fonts/raw/main/apache/robotomono/RobotoMono-Regular.ttf"
        }

        self.config = ConfigManager()
        self.login = Login(self.page, on_login_success=self.show_main_app)

        self.bot = TradeBot(db=DatabaseInterface())
        self.overlay = BotOverlay()

        self.presets = self.config.get_presets_list()
        self.header = Header(page = self.page, on_nav_click=self.on_nav_click, login=self.login)
        
        # Initialize views
        self.settings = Settings(page=self.page, config=self.config)
        self.presets = ft.Container(content=Presets(self.config, self.page, self.settings))
        # self.dashboard = ft.Container(
        #     content=Dashboard(self, self.config, self.page, self.bot, self.header),
        #     expand=True,
        # )
        self.dashboard = Dashboard(app=self, config=self.config, page=self.page, bot=self.bot, header=self.header)

        self.shop = Shop()
        
        # Pass the Header's subscription widget to the Tab so it can update status after purchase
        self.subscription_tab = SubscriptionTab(
            self.page, 
            self.login, 
            status_widget=self.header.subscription
        )

        self.header.subscription.open_subscriptions_offer.on_click = lambda e: self.go_to_subscription()

        self.body = ft.Container(content=self.dashboard, expand=True)

        self.main_column = ft.Column([self.header, self.body], expand=True)
        self.page.add(self.login)

        self.page.update()

    def show_main_app(self):
        self.header.subscription.check_subscription()
        self.page.controls.clear()
        self.page.add(self.main_column)
        self.page.update()
        #self.dashboard.update_overview()

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

    def go_to_subscription(self):
        """Switches the view to the Subscription Tab."""
        self.body.content = self.subscription_tab
        self.page.update()

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
            
            page.window.destroy()

    page.window.on_event = on_window_event
    app.page.update()


if __name__ == "__main__":
    ft.app(target=main)