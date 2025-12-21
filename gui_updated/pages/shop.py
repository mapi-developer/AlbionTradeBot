import flet as ft


class ShopingCard(ft.Column):
    def __init__(self, title: str, description: str, price: str, on_select):
        super().__init__()

        self.on_select = on_select
        self.selected = False
        self.col = {"sm": 12, "md": 4, "xl": 3}

        self.check_icon = ft.Icon(
            name=ft.Icons.CHECK_CIRCLE,
            color="#1d9dec",
            size=24,
            opacity=0,
            animate_opacity=200,
        )

        self.card_container = ft.Container(
            bgcolor="#ffffff",
            padding=20,
            border_radius=15,
            border=ft.border.all(5, ft.Colors.TRANSPARENT),
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
                                color="black",
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
                                value=price, size=22, weight="w900", color="#1d9dec"
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
                self.card_container.border = ft.border.all(5, "#1d9dec")

                self.card_container.shadow = ft.BoxShadow(
                    blur_radius=20, color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK)
                )

            else:
                self.card_container.border = ft.border.all(5, ft.Colors.TRANSPARENT)
                self.card_container.shadow = None

            self.card_container.update()

    def handle_click(self, e):
        self.on_select(self)

    def update_state(self):
        if self.selected:
            self.card_container.border = ft.border.all(5, "#1d9dec")
            self.card_container.bgcolor = "#F0F9FF"
            self.check_icon.opacity = 1

        else:
            self.card_container.border = ft.border.all(5, ft.Colors.TRANSPARENT)
            self.card_container.bgcolor = "#ffffff"
            self.check_icon.opacity = 0

        self.card_container.update()


class ShopCards(ft.ResponsiveRow):
    def __init__(self):
        super().__init__()

        self.alignment = ft.MainAxisAlignment.CENTER
        self.vertical_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 30
        self.run_spacing = 30
        self.chosen_subscription = None

        self.controls = [
            ShopingCard(
                "Starter Plan", "Full bot access for a week", "$15", self.select_plan
            ),
            ShopingCard(
                "Monthly Plan", "Full bot access for one month", "$50", self.select_plan
            ),
            ShopingCard(
                "Three Month Pass",
                "Full bot access for three months",
                "$130",
                self.select_plan,
            ),
        ]

    def select_plan(self, selected_card):
        for card in self.controls:
            card.selected = False

        selected_card.selected = True
        self.chosen_subscription = (
            selected_card.controls[0].content.controls[0].controls[1].value
        )

        for card in self.controls:
            card.update_state()


class GiftInfo(ft.Container):
    def __init__(self):
        super().__init__()
        self.margin = ft.margin.only(top=20, bottom=20)

        self.gift_checkbox = ft.Checkbox(
            label="Is it a Gift?",
            label_style=ft.TextStyle(color="white", weight="bold"),
            fill_color=ft.Colors.WHITE,
            check_color="#1d9dec",
            on_change=self.toggle_gift_fields,
            col={"sm": 4, "md": 3, "xl": 1},
        )

        self.recipient_id = ft.TextField(
            label="Recipient Email or Discord ID",
            hint_text="e.g. user@email.com",
            border_color="white",
            focused_border_color="#1d9dec",
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
    def __init__(self):
        super().__init__()
        self.padding = ft.padding.all(30)

        self.shop_cards = ShopCards()
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
                    text="Proceed to Checkout",
                    icon=ft.Icons.SHOPPING_CART,
                    style=ft.ButtonStyle(
                        color="white",
                        bgcolor="#1d9dec",
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
        plan = self.shop_cards.chosen_subscription
        is_gift = self.gift_info.gift_checkbox.value
        target_user = self.gift_info.recipient_id.value if is_gift else "Self"
        if not plan:
            print("Error: No plan selected")
        elif is_gift and not target_user:
            print("Error: Please provide recipient info")
        else:
            print(f"Purchasing {plan} for {target_user}")


def main(page: ft.Page):
    page.padding = 0
    page.title = "Subscription Shop"
    page.scroll = "auto"

    app_shop = Shop()

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
