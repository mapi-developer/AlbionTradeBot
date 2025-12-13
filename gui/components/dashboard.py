import flet as ft
import threading
import time
import keyboard
from managers.config import ConfigManager
from bot import TradeBot
from gui.components.header import Header
from database.interface import DatabaseInterface

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

        # --- Sequence State ---
        self.bot_sequence = self.config.load_bot_loop()
        self.is_running_sequence = False
        self.loop_sequence = False 

        # --- Register Global Hotkey ---
        try:
            keyboard.remove_hotkey('ctrl+p')
        except:
            pass
        
        try:
            # Note: We use a lambda or wrapper to ensure 'self' context is preserved safely
            keyboard.add_hotkey('ctrl+p', lambda: self._on_global_hotkey())
        except Exception as e:
            print(f"Failed to register global hotkey: {e}")

        # --- Tab Logic ---
        def on_tab_change(event):
            self.info_button.controls[0].content.style = ft.ButtonStyle(
                color="#ffffff", shape=ft.RoundedRectangleBorder(radius=0), bgcolor="#294D7C",
            )
            for _, control in enumerate(self.left_panel_upper_buttons.controls):
                control.content.style = ft.ButtonStyle(
                    color="#ffffff", shape=ft.RoundedRectangleBorder(radius=0), bgcolor="#294D7C",
                )

            event.control.style = ft.ButtonStyle(
                color="#ffffff", shape=ft.RoundedRectangleBorder(radius=0), bgcolor="#3E6DB3",
            )

            if event.control.data == "home":
                self.controls = [
                    ft.ResponsiveRow(
                        controls=[self.left_panel, self.home_page_tab], expand=True
                    )
                ]
                self.home_page_tab.content.controls[2] = self._create_overview_cards()

            elif event.control.data == "commands":
                if self.header.subscription.is_active:
                    self._render_sequence(should_update=False)
                    self.controls = [
                        ft.ResponsiveRow(
                            controls=[self.left_panel, self.bot_commands_tab], expand=True
                        )
                    ]
                else:
                    self.controls = [
                        ft.ResponsiveRow(
                            controls=[self.left_panel, self._create_restricted_view()], expand=True
                        )
                    ]

            elif event.control.data == "activity":
                self.controls = [
                    ft.ResponsiveRow(
                        controls=[self.left_panel, self.activity_log_tab], expand=True
                    )
                ]

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
            spacing=0,
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

        # --- Bot Commands UI Components ---
        self.available_commands_view = ft.Column(
            controls=[
                ft.Text("Available Functions", size=16, weight=ft.FontWeight.BOLD),
                ft.OutlinedButton(
                    "Add Price Check", 
                    icon=ft.Icons.ADD, 
                    on_click=lambda e: self._add_to_sequence("Price Check", "check_price"),
                    style=ft.ButtonStyle(bgcolor="#91640A", color=ft.Colors.WHITE)
                ),
                ft.OutlinedButton(
                    "Add Buy Items", 
                    icon=ft.Icons.ADD, 
                    on_click=lambda e: self._add_to_sequence("Buy Items", "buy_items"),
                    style=ft.ButtonStyle(bgcolor="#75179A", color=ft.Colors.WHITE)
                ),
                ft.OutlinedButton(
                    "Add Remove Orders", 
                    icon=ft.Icons.ADD, 
                    on_click=lambda e: self._add_to_sequence("Remove Orders", "remove_orders"),
                    style=ft.ButtonStyle(bgcolor="#203064", color=ft.Colors.WHITE)
                ),
            ],
            spacing=10
        )

        self.sequence_list_view = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO)
        self._render_sequence(should_update=False)
        
        self.loop_checkbox = ft.Checkbox(label="Repeat Loop Infinite", value=False, on_change=self._toggle_loop)
        self.status_text = ft.Text("Ready (Ctrl+P to Pause)", color=ft.Colors.GREY_400)
        
        self.run_btn = ft.ElevatedButton(
            "Run Sequence", 
            icon=ft.Icons.PLAY_ARROW, 
            on_click=self._run_sequence,
            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)
        )
        
        self.stop_btn = ft.ElevatedButton(
            "Stop", 
            icon=ft.Icons.STOP, 
            on_click=self._stop_sequence,
            style=ft.ButtonStyle(bgcolor=ft.Colors.RED_900, color=ft.Colors.WHITE),
            disabled=True
        )

        self.bot_commands_content = ft.Row(
            controls=[
                ft.Container(
                    content=self.available_commands_view,
                    col={"md": 4},
                    padding=10,
                    bgcolor="#1C2F4D",
                    border_radius=10,
                    alignment=ft.alignment.top_center
                ),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Bot Loop Sequence", size=16, weight=ft.FontWeight.BOLD),
                            ft.Container(
                                content=self.sequence_list_view,
                                bgcolor="#162238",
                                border_radius=5,
                                padding=10,
                                height=400,
                            ),
                            ft.Row(
                                controls=[self.loop_checkbox, self.status_text],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            ft.Row(controls=[self.run_btn, self.stop_btn])
                        ]
                    ),
                    col={"md": 8},
                    expand=True,
                    padding=10
                )
            ],
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.START
        )

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
                    self._create_overview_cards(),
                    ft.Divider(
                        height=2, color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE)
                    ),
                    self._create_best_orders_card(),
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            expand=True,
            col={"md": 10.5},
            padding=20,
        )

        self.bot_commands_tab = ft.Container(
            content=self.bot_commands_content, expand=True, col={"md": 10.5}, padding=20
        )

        self.activity_log_tab = ft.Container(
            content=ft.Text("Activity Log"), expand=True, col={"md": 10.5}
        )

        self.controls = [
            ft.ResponsiveRow(
                controls=[self.left_panel, self.home_page_tab], expand=True
            )
        ]

    # --- Sequence Logic ---

    def _on_global_hotkey(self):
        """Called by the keyboard library when Ctrl+P is pressed globally."""
        if not self.bot:
            return

        try:
            is_paused = self.bot.toggle_pause()
            
            # UI Updates need to be thread-safe
            if self.status_text.page:
                if is_paused:
                    self.status_text.value = "⚠️ BOT PAUSED (Press Ctrl+P to Resume)"
                    self.status_text.color = ft.Colors.ORANGE_400
                else:
                    self.status_text.value = "Bot Resumed..."
                    self.status_text.color = ft.Colors.GREEN_400
                self.status_text.update()

            if self.page:
                msg = "⏸️ Bot Paused" if is_paused else "▶️ Bot Resumed"
                color = ft.Colors.ORANGE_400 if is_paused else ft.Colors.GREEN_400
                self.page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=color)
                self.page.snack_bar.open = True
                self.page.update()
        except Exception as e:
            print(f"Hotkey Error: {e}")

    def _add_to_sequence(self, name, func):
        self.bot_sequence.append({"name": name, "func": func})
        self.config.save_bot_loop(self.bot_sequence)
        self._render_sequence()

    def _remove_from_sequence(self, index):
        if 0 <= index < len(self.bot_sequence):
            del self.bot_sequence[index]
            self.config.save_bot_loop(self.bot_sequence)
            self._render_sequence()

    def _move_item(self, index, direction):
        new_index = index + direction
        if 0 <= new_index < len(self.bot_sequence):
            self.bot_sequence[index], self.bot_sequence[new_index] = self.bot_sequence[new_index], self.bot_sequence[index]
            self.config.save_bot_loop(self.bot_sequence)
            self._render_sequence()

    def _toggle_loop(self, e):
        self.loop_sequence = e.control.value

    def _render_sequence(self, should_update=True):
        self.sequence_list_view.controls.clear()
        
        for i, item in enumerate(self.bot_sequence):
            self.sequence_list_view.controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text(f"{i+1}. {item['name']}", expand=True),
                            ft.IconButton(ft.Icons.ARROW_UPWARD, icon_size=16, on_click=lambda e, idx=i: self._move_item(idx, -1)),
                            ft.IconButton(ft.Icons.ARROW_DOWNWARD, icon_size=16, on_click=lambda e, idx=i: self._move_item(idx, 1)),
                            ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED_400, icon_size=16, on_click=lambda e, idx=i: self._remove_from_sequence(idx)),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    bgcolor="#294D7C",
                    padding=5,
                    border_radius=5
                )
            )
        if should_update and self.sequence_list_view.page:
            self.sequence_list_view.update()

    def _stop_sequence(self, e):
        # 1. Flag running as False immediately to break worker loops
        self.is_running_sequence = False
        
        self.status_text.value = "Stopping..."
        
        # 2. Reset UI buttons
        self.run_btn.disabled = False
        self.run_btn.style = ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE) # Reset color
        self.stop_btn.disabled = True
        self.available_commands_view.disabled = False
        
        if self.status_text.page:
            self.status_text.update()
        if self.run_btn.page:
            self.run_btn.update()
            self.stop_btn.update()
            self.available_commands_view.update()
            
        # 3. IMMEDIATELY delete old bot and create new one (as requested)
        print("Stopping: Replacing Bot instance...")
        try:
            self.bot = TradeBot(db=DatabaseInterface())
            if self.app:
                self.app.bot = self.bot
            self.status_text.value = "Bot Stopped & Reset."
        except Exception as ex:
            self.status_text.value = f"Error resetting bot: {ex}"
            
        if self.status_text.page:
            self.status_text.update()

    def _run_sequence(self, e):
        if not self.bot_sequence:
            self.status_text.value = "Sequence is empty!"
            self.status_text.color = ft.Colors.RED_400
            self.status_text.update()
            return

        if self.is_running_sequence:
            return

        self.is_running_sequence = True
        self.run_btn.disabled = True
        # Change color to Dark Green when running (disabled state)
        self.run_btn.style = ft.ButtonStyle(bgcolor=ft.Colors.GREEN_900, color=ft.Colors.WHITE70)
        
        self.stop_btn.disabled = False
        self.available_commands_view.disabled = True
        self.status_text.value = "Initializing Bot..."
        self.status_text.color = ft.Colors.BLUE_400
        self.update() 

        # Create new bot object to apply settings
        try:
            print("Running: Initializing new bot instance...")
            self.bot = TradeBot(db=DatabaseInterface())
            if self.app:
                self.app.bot = self.bot
        except Exception as e:
            self.status_text.value = f"Bot Init Error: {e}"
            self.status_text.color = ft.Colors.RED
            self.status_text.update()
            self.is_running_sequence = False
            self.run_btn.disabled = False
            self.run_btn.style = ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)
            self.stop_btn.disabled = True
            self.available_commands_view.disabled = False
            return

        def sequence_worker():
            try:
                while self.is_running_sequence:
                    for i, item in enumerate(self.bot_sequence):
                        if not self.is_running_sequence: break
                        if not self.bot: break 
                        
                        self._wait_if_bot_paused() 
                        if not self.is_running_sequence: break # Double check after wait
                        
                        self.status_text.value = f"Executing: {item['name']}..."
                        self.status_text.color = ft.Colors.WHITE
                        if self.status_text.page:
                            self.status_text.update()
                        
                        if self.bot:
                            func = getattr(self.bot, item["func"], None)
                            if callable(func):
                                try:
                                    func()
                                except Exception as ex:
                                    error_msg = f"Error in {item['name']}: {str(ex)}"
                                    print(error_msg)
                                    self.status_text.value = error_msg
                                    self.status_text.color = ft.Colors.RED
                                    if self.status_text.page:
                                        self.status_text.update()
                                    time.sleep(3) 
                            else:
                                 print(f"Function {item['func']} not found on bot.")

                        time.sleep(1)

                    if not self.loop_sequence:
                        break
                    
                    if self.is_running_sequence:
                        self.status_text.value = "Loop complete. Restarting..."
                        self.status_text.color = ft.Colors.CYAN_200
                        if self.status_text.page:
                            self.status_text.update()
                        time.sleep(2)

            except Exception as e:
                self.status_text.value = f"Crash: {str(e)}"
                self.status_text.color = ft.Colors.RED_900
                if self.status_text.page:
                    self.status_text.update()
                time.sleep(3)

            finally:
                # Cleanup if thread finishes naturally
                if self.is_running_sequence:
                    self.is_running_sequence = False
                    self.run_btn.disabled = False
                    self.run_btn.style = ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)
                    self.stop_btn.disabled = True
                    self.available_commands_view.disabled = False
                    self.status_text.value = "Sequence finished."
                    self.status_text.color = ft.Colors.GREY_400
                    if self.status_text.page:
                        self.status_text.update()
                    try:
                        self.update()
                    except:
                        pass

        threading.Thread(target=sequence_worker, daemon=True).start()

    def _wait_if_bot_paused(self):
        """Helper to pause the sequence runner itself between tasks."""
        # Loop while paused AND sequence is still technically running.
        # If is_running_sequence becomes False (via Stop), we break immediately.
        while self.is_running_sequence and self.bot and self.bot.paused:
            time.sleep(0.1)

    # --- Restricted View and Metrics (Existing code) ---

    def _create_restricted_view(self) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.LOCK_OUTLINE, size=80, color=ft.Colors.GREY_500),
                    ft.Text("Bot Commands Locked", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_400),
                    ft.Text("Please buy a subscription to access automated trading features.", size=14, color=ft.Colors.GREY_500),
                    ft.Container(height=20),
                    ft.ElevatedButton(
                        text="Get Subscription",
                        icon=ft.Icons.DIAMOND_OUTLINED,
                        style=ft.ButtonStyle(bgcolor="#ce7a13", color=ft.Colors.WHITE, padding=20),
                        on_click=lambda e: self.app.go_to_subscription()
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            expand=True,
            col={"md": 10.5},
            alignment=ft.alignment.center
        )

    def _create_metric_card(self, title: str, value: str, icon: str, color) -> ft.Container:
        return ft.Container(
            content=ft.Card(
                content=ft.Container(
                    padding=15,
                    content=ft.Column(
                        controls=[
                            ft.Row(controls=[ft.Icon(icon, color=ft.Colors.BLUE_ACCENT_100), ft.Text(title, size=12, color=ft.Colors.WHITE70)]),
                            ft.Column(controls=[ft.Text(value, size=24, weight=ft.FontWeight.BOLD, color=color)], spacing=5)
                        ]
                    ),
                ),
                color="#203064",
            ),
            col={"xs": 12, "sm": 6, "md": 3},
            padding=5,
        )

    def update_overview(self):
        self.home_page_tab.content.controls[2] = self._create_overview_cards()
        self.update()

    def _create_overview_cards(self) -> ft.ResponsiveRow:
        if self.bot and self.bot.db:
            db_connected = self.bot.db.check_connection_status()
            last_update = self.bot.db.get_last_update_at().strftime("%d.%m.%y | %H:%M") 
        else:
            db_connected = False
            last_update = "N/A"

        subscribed_until = self.header.subscription.subscribed_until()

        data = {
            "Last Prices Update (UTC)": (last_update, ft.Icons.UPDATE, ft.Colors.WHITE),
            "Database Status": ("Connected" if db_connected else "Connection Error", ft.Icons.ACCOUNT_TREE, "#089E28" if db_connected else "#9A2D08"),
            "Bot Status": (self.bot.status, ft.Icons.ADB, "#089E28"),
            "Subscribed until": (subscribed_until, ft.Icons.ADD_TASK, ft.Colors.WHITE),
        }

        cards = []
        for title, (value, icon, color) in data.items():
            cards.append(self._create_metric_card(title, value, icon, color))

        return ft.ResponsiveRow(controls=cards, run_spacing={"xs": 0}, spacing=10)

    def _create_best_orders_card(self) -> ft.Card:
        best_orders_data = [
            {"name": "Epic Sword", "unique_name": "sword_epic_01", "image_url": "https://render.albiononline.com/v1/item/T8_HEAD_CLOTH_KEEPER", "order_price": 12000, "bm_price": 18000, "profit": 6000},
            {"name": "Rare Potion", "unique_name": "potion_rare_03", "image_url": "https://render.albiononline.com/v1/item/T6_POTION_HEAL", "order_price": 500, "bm_price": 950, "profit": 450},
        ]
        rows = []
        for item in best_orders_data:
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Row([ft.Image(src=item["image_url"], width=30, height=30), ft.Column([ft.Text(item["name"], weight=ft.FontWeight.BOLD, size=14), ft.Text(item["unique_name"], size=10, color=ft.Colors.WHITE54)], spacing=0)])),
                ft.DataCell(ft.Text(f"${item['order_price']:,}")),
                ft.DataCell(ft.Text(f"${item['bm_price']:,}")),
                ft.DataCell(ft.Text(f"${item['profit']:,}", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_ACCENT_400)),
            ]))
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[ft.Text("Last 10 Best Orders Made 📈", size=18, weight=ft.FontWeight.BOLD), ft.DataTable(columns=[ft.DataColumn(ft.Text("Item", weight=ft.FontWeight.BOLD)), ft.DataColumn(ft.Text("Order Price", weight=ft.FontWeight.BOLD), numeric=True), ft.DataColumn(ft.Text("BM Price", weight=ft.FontWeight.BOLD), numeric=True), ft.DataColumn(ft.Text("Profit", weight=ft.FontWeight.BOLD), numeric=True)], rows=rows, column_spacing=25, bgcolor="#294D7C")],
                    spacing=15,
                ),
                padding=20,
            ),
            expand=True,
        )