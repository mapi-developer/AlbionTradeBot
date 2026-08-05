import os
import sys
from datetime import datetime, timezone
import flet as ft
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.components.style import GuiStyle
from pages.login import Login

API_URL = "https://trade-backend-service-1014783260724.europe-west1.run.app"


class Subscription(ft.Container):
    def __init__(self, page: ft.Page, login: Login, on_payment_click=None):
        self.login = login
        self.state = login.state
        self.on_payment_click = on_payment_click  # Callback to redirect to Shop
        self.is_active = False  # Flag to be accessed by Dashboard

        self.open_subscriptions_offer = ft.ElevatedButton(
            content=ft.Text("Buy Subscription"),
            icon=ft.Icons.CURRENCY_BITCOIN,
            style=ft.ButtonStyle(
                bgcolor=GuiStyle.Colors.ACCENT_ORANGE,
                color=ft.Colors.WHITE,
            ),
            on_click=self.pay_click,
        )

        self.status_text = ft.Text(
            "Status Loading...",
            size=12,
            color=GuiStyle.Colors.ACCENT_GREEN,
            weight=ft.FontWeight.BOLD,
        )

        # Fixed: Changed `ft.padding.only` back to `ft.Padding.only`
        self.status = ft.Container(
            content=self.status_text,
            padding=ft.Padding.only(right=20),
        )

        super().__init__(
            content=ft.Row(
                controls=[
                    self.status,
                    self.open_subscriptions_offer,
                ]
            )
        )

    def did_mount(self):
        """Fires automatically after the control is added to the page tree."""
        self.check_subscription()

    def check_subscription(self):
        self.state = self.login.state
        if not self.state.user_id or not self.state.token:
            self.is_active = False
            self.status_text.value = "Not Logged In"
            self.status_text.color = GuiStyle.Colors.ACCENT_ORANGE
            self.open_subscriptions_offer.visible = True
            self.update()
            return

        headers = {"Authorization": f"Bearer {self.state.token}"}
        try:
            res = requests.get(
                f"{API_URL}/users/{self.state.user_id}", headers=headers
            )

            if res.status_code == 200:
                data = res.json()
                sub_date = data.get("subscribed_until")

                if sub_date:
                    try:
                        parsed_date = datetime.strptime(
                            sub_date, "%Y-%m-%dT%H:%M:%S.%f%z"
                        )
                    except ValueError:
                        parsed_date = datetime.fromisoformat(sub_date)

                    if parsed_date < datetime.now(timezone.utc):
                        self.status_text.value = "Subscription expired"
                        self.status_text.color = GuiStyle.Colors.ACCENT_RED
                        self.open_subscriptions_offer.visible = True
                        self.is_active = False
                    else:
                        self.status_text.value = "Subscription active"
                        self.status_text.color = GuiStyle.Colors.ACCENT_GREEN
                        self.open_subscriptions_offer.visible = False
                        self.is_active = True
                else:
                    self.status_text.value = "Subscription not active"
                    self.open_subscriptions_offer.visible = True
                    self.status_text.color = GuiStyle.Colors.ACCENT_ORANGE
                    self.is_active = False

                self.update()

            elif res.status_code == 404:
                print("Error to check subscription status")
                self.is_active = False
                self.update()

        except Exception as e:
            print(f"Connection error during status check: {e}")
            self.is_active = False
            try:
                self.update()
            except RuntimeError:
                pass

    def pay_click(self, e):
        if self.on_payment_click:
            self.on_payment_click()