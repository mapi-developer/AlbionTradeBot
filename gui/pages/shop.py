import flet as ft
import requests
import webbrowser
import re
from typing import TYPE_CHECKING

from components.style import GuiStyle
from components import show_popup
from bot import SettingsHandler

if TYPE_CHECKING:
    from pages import State


class ShopingCard(ft.Column):
    def __init__(self, title: str, description: str, price: str, plan_id: str, on_select):
        super().__init__()
        self.on_select = on_select
        self.selected = False
        self.plan_id = plan_id 
        self.col = {"sm": 12, "md": 4, "xl": 3}

        self.check_icon = ft.Icon(
            icon=ft.Icons.CHECK_CIRCLE,
            color=GuiStyle.Colors.WHITE,
            size=24,
            opacity=0,
            animate_opacity=200,
        )

        self.card_container = ft.Container(
            bgcolor=GuiStyle.Colors.CARD_BG,
            padding=20,
            border_radius=15,
            border=ft.Border.all(5, ft.Colors.TRANSPARENT),
            animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
            on_hover=self.handle_hover,
            on_click=self.handle_click,
            content=ft.Column(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Container(height=10),
                            ft.Text(
                                value=title,
                                size=20,
                                weight="bold",
                                color=GuiStyle.Colors.WHITE,
                                text_align=ft.TextAlign.CENTER,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Text(
                                value=description,
                                size=14,
                                color="grey",
                                text_align=ft.TextAlign.CENTER,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        controls=[
                            self.check_icon,
                            ft.Text(
                                value=price, size=22, weight="w900", color=GuiStyle.Colors.WHITE
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN, 
            ),
        )

        self.controls = [self.card_container]

    def handle_hover(self, e):
        if not self.selected:
            if e.data == "true":
                self.card_container.border = ft.Border.all(5, GuiStyle.Colors.BORDER_DEFAULT)

                self.card_container.shadow = ft.BoxShadow(
                    blur_radius=20, color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK)
                )

            else:
                self.card_container.border = ft.Border.all(5, ft.Colors.TRANSPARENT)
                self.card_container.shadow = None

            self.card_container.update()

    def handle_click(self, e):
        self.on_select(self)

    def update_state(self):
        if self.selected:
            self.card_container.border = ft.Border.all(5, GuiStyle.Colors.WHITE)
            self.card_container.bgcolor = GuiStyle.Colors.CARD_BG
            self.check_icon.opacity = 1
        else:
            self.card_container.border = ft.Border.all(5, ft.Colors.TRANSPARENT)
            self.card_container.bgcolor = GuiStyle.Colors.CARD_BG
            self.check_icon.opacity = 0

        self.card_container.update()


class ShopCards(ft.ResponsiveRow):
    def __init__(self, api_url):
        super().__init__()
        self.api_url = api_url
        self.alignment = ft.MainAxisAlignment.CENTER
        self.vertical_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 30
        self.run_spacing = 30
        self.chosen_plan_id = None 
        self.chosen_subscription_name = None

        plans_data = {
            "1_week": {"price": 14.90, "days": 7},
            "1_month": {"price": 49.90, "days": 30},
            "3_months": {"price": 124.90, "days": 90},
        }
        try:
            res = requests.get(f"{self.api_url}/payments/plans", timeout=5)
            
            if res.status_code == 200:
                plans_data = res.json()
        except: pass

        self.controls = [
            ShopingCard(
                "Starter Pass", "Full bot access for a week", f"${plans_data["1_week"]["price"]}", "1_week", self.select_plan
            ),
            ShopingCard(
                "Monthly Pass", "Full bot access for one month", f"${plans_data["1_month"]["price"]}", "1_month", self.select_plan
            ),
            ShopingCard(
                "Three Month Pass",
                "Full bot access for three months",
                f"${plans_data["3_months"]["price"]}", 
                "3_months",
                self.select_plan,
            ),
        ]

    def select_plan(self, selected_card):
        for card in self.controls:
            card.selected = False

        selected_card.selected = True
        self.chosen_subscription_name = (
            selected_card.controls[0].content.controls[0].controls[1].value
        )
        self.chosen_plan_id = selected_card.plan_id

        for card in self.controls:
            card.update_state()


class GiftInfo(ft.Container):
    def __init__(self):
        super().__init__()
        self.margin = ft.Margin.only(top=20, bottom=20)

        self.gift_checkbox = ft.Checkbox(
            label="Is it a Gift?",
            label_style=ft.TextStyle(color="white", weight="bold"),
            fill_color=ft.Colors.WHITE,
            check_color=GuiStyle.Colors.ACCENT_BLUE,
            on_change=self.toggle_gift_fields,
            col={"sm": 4, "md": 3, "xl": 1},
        )

        self.recipient_id = ft.TextField(
            label="Recipient User ID",
            hint_text="e.g. 123",
            border_color="white",
            focused_border_color=GuiStyle.Colors.ACCENT_BLUE,
            label_style=ft.TextStyle(color="white"),
            color="white",
            text_size=14,
            disabled=True,
            opacity=0,
            animate_opacity=300,
            col={"sm": 8, "md": 9, "xl": 5},
        )

        # ResponsiveRow inside a fixed-width container to allow centering on XL
        self.inner_row = ft.ResponsiveRow(
            controls=[self.gift_checkbox, self.recipient_id],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self.content = ft.Container(
            content=self.inner_row,
        )

    def toggle_gift_fields(self, e):
        self.recipient_id.disabled = not self.gift_checkbox.value
        self.recipient_id.opacity = 1.0 if self.gift_checkbox.value else 0
        self.update()

    def update_alignment(self, width):
        if width < 800:
            self.inner_row.alignment = ft.MainAxisAlignment.SPACE_BETWEEN
        else:
            self.inner_row.alignment = ft.MainAxisAlignment.CENTER
        self.update()


class Shop(ft.Container):
    def __init__(self, settings: SettingsHandler, login_state: "State", page=None):
        super().__init__()
        self.settings = settings
        self.padding = ft.Padding.all(30)
        self.login_state = login_state

        self.shop_cards = ShopCards(self.settings.API_URL)
        self.gift_info = GiftInfo()

        self.content = ft.Column(
            controls=[
                ft.Text(
                    "Available Subscriptions", size=28, weight="bold", color="white"
                ),
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                self.shop_cards,
                self.gift_info,
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                ft.ElevatedButton(
                    content=ft.Text("Proceed to Checkout"),
                    icon=ft.Icons.SHOPPING_CART,
                    style=ft.ButtonStyle(
                        color="white",
                        bgcolor=GuiStyle.Colors.ACCENT_BLUE,
                        padding=20,
                        shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                    width=300,
                    on_click=self.on_purchase_click,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            tight=True,
        )

    def on_purchase_click(self, e):
        print("Purchase")
        plan_id = self.shop_cards.chosen_plan_id
        is_gift = self.gift_info.gift_checkbox.value
        
        if is_gift:
             print("gift")
             target_user_id = re.sub(r"\s+", "", self.gift_info.recipient_id.value)
        elif self.login_state:
             print("not gift")
             target_user_id = self.login_state.user_id
        else:
             print("Error to find user")
             target_user_id = None

        if not plan_id:
            self.show_snack("Error: No plan selected")
            return
        
        if not target_user_id:
            self.show_snack("Error: Please provide recipient ID or login first")
            return

        try:
            res = requests.post(
                f"{self.settings.API_URL}/payments/create", 
                params={"user_id": target_user_id},
                json={"plan_id": plan_id}
            )
            
            if res.status_code == 200:
                data = res.json()
                invoice_url = data.get("invoice_url")
                if invoice_url:
                    webbrowser.open(invoice_url)
                    self.show_snack("Redirecting to payment provider...")
                else:
                    self.show_snack("Error: Payment URL not found")
            else:
                self.show_snack(f"Error starting payment: {res.status_code}")

        except Exception as ex:
            print(ex)
            self.show_snack(f"Connection Error: {ex}")

    def show_snack(self, message):
        try:
            show_popup(self.page, message)
            self.page.update()
        except RuntimeError:
            pass


def main(page: ft.Page):
    page.padding = 0
    page.title = "Subscription Shop"
    page.scroll = ft.ScrollMode.AUTO
    
    class MockState:
        user_id = 1
        
    app_shop = Shop(login_state=MockState(), page=page)

    def on_page_resize(e):
        app_shop.gift_info.update_alignment(page.window.width)

    page.on_resize = on_page_resize
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    page.add(app_shop)

    app_shop.gift_info.update_alignment(page.window.width)
    page.update()


if __name__ == "__main__":
    ft.app(target=main)