import flet as ft
import requests
from .login import Login
from datetime import datetime, timezone
import threading
import webbrowser
import time

API_URL = "https://crypto-backend-736893217724.europe-west3.run.app"

class Subscription(ft.Container):
    def __init__(self, page: ft.Page, login: Login):
        super().__init__()
        self.login = login
        self.state = login.state
        self.page = page

        self.open_subscriptions_offer = ft.ElevatedButton(
            text="Buy Sibscribtion", 
            #on_click=pay_click, 
            icon=ft.Icons.CURRENCY_BITCOIN,
            style=ft.ButtonStyle(bgcolor="#ce7a13", color=ft.Colors.WHITE),
            on_click=self.pay_click
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
            return
        
        headers = {"Authorization": f"Bearer {self.state.token}"}
        try:
            res = requests.get(f"{API_URL}/users/{self.state.user_id}", headers=headers)
            
            if res.status_code == 200:
                data = res.json()
                sub_date = data.get("subscribed_until")
                
                if sub_date:
                    if datetime.strptime(sub_date, '%Y-%m-%dT%H:%M:%S.%f%z') < datetime.now(timezone.utc):
                        return "Expired!"
                    else:
                        return datetime.strptime(sub_date, '%Y-%m-%dT%H:%M:%S.%f%z').strftime()
                else:
                    return "No Subscribtion"
            elif res.status_code == 404:
                return "Error"
            
        except Exception as e:
            print(f"Connection error during status check: {e}")

    def check_subscription(self):
        self.state = self.login.state
        if not self.state.user_id or not self.state.token: 
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
                    else:
                        self.status.content.value = "Subscription active"
                        self.open_subscriptions_offer.visible = False
                else:
                    self.status.content.value = "Subscription not active"
                    self.open_subscriptions_offer.visible = True
                
                self.page.update()
            
            elif res.status_code == 404:
                print("Error to check subscription status")
            
            self.page.update()

        except Exception as e:
            print(f"Connection error during status check: {e}")
            self.page.update()

    def pay_click(self, e):
        """Starts payment flow"""
        if not self.state.user_id or not self.state.token: 
            self.page.update()
            return

        self.page.update()

        try:
            res = requests.post(f"{API_URL}/payments/create", 
                                params={"user_id": self.state.user_id, "plan_id": "1_week"})
            
            if res.status_code == 200:
                data = res.json()
                webbrowser.open(data.get("invoice_url"))
                threading.Thread(target=self.poll_payment_status, daemon=True).start()
            else:
                print(res.text)

        except Exception as ex:
            print(ex)
        self.page.update()

    def poll_payment_status(self):
        """Checks subscription status every 5 seconds (runs in background thread)."""
        for _ in range(60): 
            time.sleep(5)
            # Safe to call because check_subscription calls page.update() which is thread-safe
            self.check_subscription() 
            if self.status.content.value == "Subscription active":
                break