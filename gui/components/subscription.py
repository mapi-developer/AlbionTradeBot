import flet as ft
import requests
from datetime import datetime, timezone
import threading
import webbrowser
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pages.login import Login


API_URL = "https://crypto-backend-736893217724.europe-west3.run.app"

class Subscription(ft.Container):
    """
    Small widget used in the Header to show status.
    """
    def __init__(self, page: ft.Page, login: Login):
        super().__init__()
        self.login = login
        self.state = login.state
        self.page = page
        self.is_active = False # Flag to be accessed by Dashboard

        self.open_subscriptions_offer = ft.ElevatedButton(
            text="Buy Subscription", 
            icon=ft.Icons.CURRENCY_BITCOIN,
            style=ft.ButtonStyle(bgcolor="#ce7a13", color=ft.Colors.WHITE)
        )

        self.status = ft.Container(
            ft.Text(
                "Status Loading...",
                style=ft.TextStyle(
                    size=12,
                    color="#1f9f06"
                ),
            ),
            padding=ft.padding.only(0, 0, 20, 0)
        )

        self.check_subscription()

        self.content = ft.Row(
            controls=[
                self.status,
                self.open_subscriptions_offer
            ]
        )

    def subscribed_until(self) -> str:
        self.state = self.login.state
        if not self.state.user_id or not self.state.token:
            return "Not Logged In"
        
        headers = {"Authorization": f"Bearer {self.state.token}"}
        try:
            res = requests.get(f"{API_URL}/users/{self.state.user_id}", headers=headers)
            
            if res.status_code == 200:
                data = res.json()
                sub_date = data.get("subscribed_until")
                
                if sub_date:
                    if datetime.strptime(sub_date, '%Y-%m-%dT%H:%M:%S.%f%z') < datetime.now(timezone.utc):
                        self.is_active = False
                        return "Expired!"
                    else:
                        self.is_active = True
                        return datetime.strptime(sub_date, '%Y-%m-%dT%H:%M:%S.%f%z').strftime("%d.%m.%y")
                else:
                    self.is_active = False
                    return "No Subscription"
            elif res.status_code == 404:
                self.is_active = False
                return "Error"
            
        except Exception as e:
            print(f"Connection error during status check: {e}")
            return "Error"

    def check_subscription(self):
        self.state = self.login.state
        if not self.state.user_id or not self.state.token: 
            self.is_active = False
            self.page.update()
            return
        
        headers = {"Authorization": f"Bearer {self.state.token}"}
        try:
            res = requests.get(f"{API_URL}/users/{self.state.user_id}", headers=headers)
            
            if res.status_code == 200:
                data = res.json()
                sub_date = data.get("subscribed_until")
                
                if sub_date:
                    if datetime.strptime(sub_date, '%Y-%m-%dT%H:%M:%S.%f%z') < datetime.now(timezone.utc):
                        self.status.content.value = "Subscription expired"
                        self.status.content.style.color = "#efaa08"
                        self.open_subscriptions_offer.visible = True
                        self.is_active = False
                    else:
                        self.status.content.value = "Subscription active"
                        self.open_subscriptions_offer.visible = False
                        self.is_active = True
                else:
                    self.status.content.value = "Subscription not active"
                    self.open_subscriptions_offer.visible = True
                    self.is_active = False
                
                self.page.update()
            
            elif res.status_code == 404:
                print("Error to check subscription status")
                self.is_active = False
            
            self.page.update()

        except Exception as e:
            print(f"Connection error during status check: {e}")
            self.is_active = False
            self.page.update()

    def pay_click(self, e):
        # Default payment click from header (defaults to 1 week or opens tab)
        # Ideally this should redirect to the main SubscriptionTab
        pass

class SubscriptionTab(ft.Container):
    """
    The full view tab for selecting a subscription plan.
    """
    def __init__(self, page: ft.Page, login: Login, status_widget: Subscription):
        super().__init__()
        self.page = page
        self.login = login
        self.status_widget = status_widget # Reference to update status after payment
        self.expand = True
        self.padding = 30
        
        self.content = ft.Column(
            controls=[
                ft.Text("Choose your Plan", size=30, weight=ft.FontWeight.BOLD),
                ft.Divider(color=ft.Colors.TRANSPARENT, height=20),
                ft.ResponsiveRow(
                    controls=[
                        self._create_plan_card("1 Week", "1_week", "0.001 BTC", ft.Icons.CALENDAR_VIEW_WEEK),
                        self._create_plan_card("1 Month", "1_month", "0.003 BTC", ft.Icons.DATE_RANGE),
                        self._create_plan_card("3 Months", "3_months", "0.008 BTC", ft.Icons.CALENDAR_MONTH),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

    def _create_plan_card(self, title, plan_id, price, icon):
        return ft.Container(
            col={"sm": 12, "md": 4},
            content=ft.Container(
                bgcolor="#294D7C",
                border_radius=15,
                padding=30,
                content=ft.Column(
                    controls=[
                        ft.Icon(icon, size=40, color=ft.Colors.WHITE70),
                        ft.Text(title, size=24, weight=ft.FontWeight.BOLD),
                        ft.Text(price, size=20, color="#efaa08", weight=ft.FontWeight.BOLD),
                        ft.Container(height=20),
                        ft.ElevatedButton(
                            text="Buy Now",
                            style=ft.ButtonStyle(
                                bgcolor="#ce7a13", 
                                color=ft.Colors.WHITE,
                                shape=ft.RoundedRectangleBorder(radius=8),
                                padding=20
                            ),
                            width=150,
                            on_click=lambda e: self.pay_click(plan_id)
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10
                )
            )
        )

    def pay_click(self, plan_id):
        state = self.login.state
        if not state.user_id or not state.token: 
            self.page.snack_bar = ft.SnackBar(ft.Text("Please login first!"))
            self.page.snack_bar.open = True
            self.page.update()
            return

        try:
            res = requests.post(f"{API_URL}/payments/create", 
                                params={"user_id": state.user_id, "plan_id": plan_id})
            
            if res.status_code == 200:
                data = res.json()
                webbrowser.open(data.get("invoice_url"))
                
                # Start polling on the status widget
                threading.Thread(target=self.status_widget.poll_payment_status, daemon=True).start()
            else:
                print(res.text)

        except Exception as ex:
            print(ex)