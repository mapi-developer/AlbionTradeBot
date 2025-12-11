import flet as ft
from managers.config import ConfigManager
from bot import TradeBot
from gui.components.header import Header

class Dashboard(ft.Column):
    bot: TradeBot

    def __init__(self, app, config: ConfigManager, page: ft.Page, bot: TradeBot, header: Header):
        super().__init__()
        self.app = app
        self.header = header
        self.config = config
        self.page = page
        self.bot = bot
        self.expand = True

        # --- Tab Logic ---
        def on_tab_change(event):
            self.info_button.controls[0].content.style = ft.ButtonStyle(
                color="#ffffff",
                shape=ft.RoundedRectangleBorder(radius=0),
                bgcolor="#294D7C",
            )
            for _, control in enumerate(self.left_panel_upper_buttons.controls):
                control.content.style = ft.ButtonStyle(
                    color="#ffffff",
                    shape=ft.RoundedRectangleBorder(radius=0),
                    bgcolor="#294D7C",
                )

            event.control.style = ft.ButtonStyle(
                color="#ffffff",
                shape=ft.RoundedRectangleBorder(radius=0),
                bgcolor="#3E6DB3",
            )

            if event.control.data == "home":
                self.controls = [
                    ft.ResponsiveRow(
                        controls=[self.left_panel, self.home_page_tab], expand=True
                    )
                ]
            elif event.control.data == "commands":
                self.controls = [
                    ft.ResponsiveRow(
                        controls=[self.left_panel, self.bot_commands_tab], expand=True
                    )
                ]
            elif event.control.data == "activity":
                self.controls = [
                    ft.ResponsiveRow(
                        controls=[self.left_panel, self.activity_log_tab], expand=True
                    )
                ]
            else:
                print(f"No Tab found: {event.control.data}")
            
            self.home_page_tab.content.controls[2] = self._create_overview_cards()

            self.update()

        self.page.update()

        # --- Sidebar Buttons ---
        self.left_panel_upper_buttons = ft.Column(
            controls=[
                ft.Container(
                    content=ft.ElevatedButton(
                        text="Home Page",
                        data="home",
                        on_click=on_tab_change,
                        style=ft.ButtonStyle(
                            color="#ffffff",
                            shape=ft.RoundedRectangleBorder(radius=0),
                            bgcolor="#3E6DB3",
                        ),
                    ),
                ),
                ft.Container(
                    content=ft.ElevatedButton(
                        text="Bot Commands",
                        data="commands",
                        on_click=on_tab_change,
                        style=ft.ButtonStyle(
                            color="#ffffff",
                            shape=ft.RoundedRectangleBorder(radius=0),
                            bgcolor="#294D7C",
                        ),
                    ),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            spacing=0,  # Spacing removed between buttons
        )

        self.info_button = ft.Column(
            controls=[
                ft.Container(
                    content=ft.ElevatedButton(
                        text="Activity Log",
                        data="activity",
                        on_click=on_tab_change,
                        icon=ft.Icons.INFO_OUTLINE,
                        style=ft.ButtonStyle(
                            color="#ffffff",
                            shape=ft.RoundedRectangleBorder(radius=0),
                            bgcolor="#294D7C",
                        ),
                    ),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            spacing=0,
        )

        self.left_panel_content = ft.Column(
            controls=[self.left_panel_upper_buttons, self.info_button],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        self.left_panel = ft.Container(
            content=self.left_panel_content,
            bgcolor="#294D7C",
            col={"md": 1.5},
            expand=True,
        )

        # --- Bot Commands Content ---
        self.bot_buttons = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.OutlinedButton(
                            "Check Prices",
                            style=ft.ButtonStyle(
                                color=ft.Colors.WHITE,
                                bgcolor="#91640A",
                                shape=ft.RoundedRectangleBorder(radius=8),
                                side=ft.BorderSide(1, "#CB9935"),
                            ),
                            on_click=lambda e: app.run_bot("check_price")
                        ),
                        ft.OutlinedButton(
                            "Buy Items",
                            style=ft.ButtonStyle(
                                color=ft.Colors.WHITE,
                                bgcolor="#75179A",
                                shape=ft.RoundedRectangleBorder(radius=8),
                                side=ft.BorderSide(1, "#9A26AE"),
                            ),
                            on_click=lambda e: app.run_bot("buy_items")
                        ),
                    ]
                )
            ]
        )

        # --- Home Page Content ---
        self.overview_row = ft.Row(
            controls=[
                ft.Text(
                    "Trade Bot overview:",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                )
            ]
        )

        self.home_page_tab = ft.Container(
            content=ft.Column(
                controls=[
                    self.overview_row,
                    ft.Divider(
                        height=2, color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE)
                    ),
                    self._create_overview_cards(),  # The key metrics cards
                    ft.Divider(
                        height=2, color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE)
                    ),
                    self._create_best_orders_card(),  # The list of best orders
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            expand=True,
            col={"md": 10.5},
            padding=20,
        )

        self.bot_commands_tab = ft.Container(
            content=self.bot_buttons, expand=True, col={"md": 10.5}
        )

        self.activity_log_tab = ft.Container(
            content=ft.Text("Activity Log"), expand=True, col={"md": 10.5}
        )

        self.controls = [
            ft.ResponsiveRow(
                controls=[self.left_panel, self.home_page_tab], expand=True
            )
        ]

    def _create_metric_card(
        self, title: str, value: str, icon: str, color
    ) -> ft.Container:
        """Helper to create a single consistent metric card."""
        return ft.Container(
            content=ft.Card(
                content=ft.Container(
                    padding=15,
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(icon, color=ft.Colors.BLUE_ACCENT_100),
                                    ft.Text(title, size=12, color=ft.Colors.WHITE70),
                                ]
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        value, size=24, weight=ft.FontWeight.BOLD, color=color
                                    ),
                                ],
                                spacing=5,
                            )
                        ]
                    ),
                ),
                color="#203064",  # Darker color for the card background
            ),
            col={"xs": 12, "sm": 6, "md": 3},
            padding=5,
        )

    def update_overview(self):
        self.home_page_tab.content.controls[2] = self._create_overview_cards()
        self.update()

    def _create_overview_cards(self) -> ft.ResponsiveRow:
        db_connected = self.bot.db.check_connection_status()
        last_update = self.bot.db.get_last_update_at().strftime("%d.%m.%y | %H:%M") 
        subscribed_until = self.header.subscription.subscribed_until()

        data = {
            "Last Prices Update (UTC)": (last_update, ft.Icons.UPDATE, ft.Colors.WHITE),
            "Database Status": ("Connected" if db_connected else "Connection Error", ft.Icons.ACCOUNT_TREE, "#089E28" if db_connected else "#9A2D08"),
            "Bot Status": ("Ready", ft.Icons.ADB, "#089E28"),
            "Subscribed until": (subscribed_until, ft.Icons.ADD_TASK, ft.Colors.WHITE),
        }

        cards = []
        for title, (value, icon, color) in data.items():
            cards.append(self._create_metric_card(title, value, icon, color))

        return ft.ResponsiveRow(controls=cards, run_spacing={"xs": 0}, spacing=10)

    def _create_best_orders_card(self) -> ft.Card:
        # Placeholder Data
        best_orders_data = [
            {
                "name": "Epic Sword",
                "unique_name": "sword_epic_01",
                "image_url": "https://render.albiononline.com/v1/item/T8_HEAD_CLOTH_KEEPER",
                "order_price": 12000,
                "bm_price": 18000,
                "profit": 6000,
            },
            {
                "name": "Rare Potion",
                "unique_name": "potion_rare_03",
                "image_url": "https://render.albiononline.com/v1/item/T6_POTION_HEAL",
                "order_price": 500,
                "bm_price": 950,
                "profit": 450,
            },
        ]

        # Convert data into DataTable format
        rows = []
        for item in best_orders_data:
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Row(
                                [
                                    ft.Image(
                                        src=item["image_url"], width=30, height=30
                                    ),
                                    ft.Column(
                                        [
                                            ft.Text(
                                                item["name"],
                                                weight=ft.FontWeight.BOLD,
                                                size=14,
                                            ),
                                            ft.Text(
                                                item["unique_name"],
                                                size=10,
                                                color=ft.Colors.WHITE54,
                                            ),
                                        ],
                                        spacing=0,
                                    ),
                                ]
                            )
                        ),
                        ft.DataCell(ft.Text(f"${item['order_price']:,}")),
                        ft.DataCell(ft.Text(f"${item['bm_price']:,}")),
                        ft.DataCell(
                            ft.Text(
                                f"${item['profit']:,}",
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.GREEN_ACCENT_400,
                            )
                        ),
                    ]
                )
            )

        data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Item", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(
                    ft.Text("Order Price", weight=ft.FontWeight.BOLD), numeric=True
                ),
                ft.DataColumn(
                    ft.Text("BM Price", weight=ft.FontWeight.BOLD), numeric=True
                ),
                ft.DataColumn(
                    ft.Text("Profit", weight=ft.FontWeight.BOLD), numeric=True
                ),
            ],
            rows=rows,
            column_spacing=25,
            bgcolor="#294D7C",
        )

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Last 10 Best Orders Made 📈",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                        ),
                        data_table,
                    ],
                    spacing=15,
                ),
                padding=20,
            ),
            expand=True,
        )
