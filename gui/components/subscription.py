import flet as ft
import requests
from .login import Login
from datetime import datetime, timezone

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