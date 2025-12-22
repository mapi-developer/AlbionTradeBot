import flet as ft
import asyncio
import uuid


class LeftPanelButton(ft.Container):
    def __init__(self, text: str, data: str):
        super().__init__()
        self.padding = 0
        self.col = {"sm": 12, "md": 12, "xl": 12}
        self.content = ft.ElevatedButton(
            text=text,
            data=data,
            style=ft.ButtonStyle(
                color="#ffffff",
                shape=ft.RoundedRectangleBorder(radius=0),
                bgcolor="#225BA1",
                shadow_color=ft.Colors.TRANSPARENT,
                text_style=ft.TextStyle(size=18),
                padding=ft.padding.only(0, 15, 0, 15),
            ),
        )


class LeftPanel(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.spacing = 0

        dashboard_panel_button = LeftPanelButton("Dashboard", "dashboard")
        sequence_panel_button = LeftPanelButton("Bot Sequence", "sequence")
        logs_panel_button = LeftPanelButton("Activity Logs", "logs")

        self.dashboard_button = dashboard_panel_button.content
        self.sequence_button = sequence_panel_button.content
        self.logs_button = logs_panel_button.content

        self.upper_buttons = ft.Column(
            spacing=0,
            controls=[
                ft.ResponsiveRow(
                    spacing=0,
                    run_spacing=0,
                    controls=[
                        self.dashboard_button,
                        self.sequence_button,
                    ],
                )
            ],
        )

        self.lower_buttons = ft.Column(
            spacing=0,
            controls=[
                ft.ResponsiveRow(
                    spacing=0,
                    run_spacing=0,
                    controls=[self.logs_button],
                )
            ],
        )

        self.col = {"sm": 1.5, "md": 1.5, "xl": 1.5}
        self.controls = [
            ft.Container(
                expand=True,
                alignment=ft.alignment.top_left,
                content=ft.Column(
                    spacing=0,
                    controls=[self.upper_buttons, self.lower_buttons],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                bgcolor="#1C416C",
            )
        ]


class InfoCard(ft.Container):
    def __init__(self, title: str, icon: str, value: str = "Data Loading..."):
        super().__init__()

        self.col = {"xs": 12, "sm": 6, "md": 3}
        self.content = ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column(
                    controls=[
                        ft.ResponsiveRow(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Icon(icon, color=ft.Colors.BLUE_ACCENT_100),
                                        ft.Text(
                                            title, size=12, color=ft.Colors.WHITE70
                                        ),
                                    ]
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            value=value,
                                            size=24,
                                            weight=ft.FontWeight.BOLD,
                                            color="#ffffff",
                                        )
                                    ],
                                    spacing=5,
                                ),
                            ]
                        ),
                    ]
                ),
            ),
            color="#203064",
        )

        self.value_text = (
            self.content.content.content.controls[0].controls[1].controls[0]
        )

    def update_data(self, value: str):
        self.value_text.value = value
        self.update()


class OverviewPanel(ft.Container):
    def __init__(self):
        super().__init__()

        self.last_prices_update = InfoCard(
            title="Last Prices Update (UTC)", icon=ft.Icons.UPDATE
        )
        self.database_status = InfoCard(
            title="Database Status", icon=ft.Icons.ACCOUNT_TREE
        )
        self.bot_status = InfoCard(title="Bot Status", icon=ft.Icons.ADB)
        self.subscribed_until = InfoCard(
            title="Subscribed until", icon=ft.Icons.ADD_TASK
        )

        self.content = ft.ResponsiveRow(
            controls=[
                self.last_prices_update,
                self.database_status,
                self.bot_status,
                self.subscribed_until,
            ],
            spacing=5,
        )


class OrdersGraph(ft.Container):
    def __init__(self, max_y: int = 40):
        super().__init__()
        self.padding = 20
        self.bgcolor = "#203064"
        self.border_radius = 10
        self.margin = ft.margin.only(top=10)

        self.chart_data = [
            ft.LineChartDataPoint(0, 5),
            ft.LineChartDataPoint(1, 12),
            ft.LineChartDataPoint(2, 8),
            ft.LineChartDataPoint(3, 25),
            ft.LineChartDataPoint(4, 15),
            ft.LineChartDataPoint(5, 30),
            ft.LineChartDataPoint(6, 22),
            ft.LineChartDataPoint(7, 5),
            ft.LineChartDataPoint(8, 12),
            ft.LineChartDataPoint(9, 8),
            ft.LineChartDataPoint(10, 25),
        ]

        self.chart = ft.LineChart(
            data_series=[
                ft.LineChartData(
                    data_points=self.chart_data,
                    stroke_width=4,
                    color=ft.Colors.WHITE70,
                    curved=False,
                    point=True,
                )
            ],
            bottom_axis=ft.ChartAxis(
                labels=[
                    ft.ChartAxisLabel(value=2, label=ft.Text("2d ago", size=15)),
                    ft.ChartAxisLabel(value=4, label=ft.Text("1d 12h ago", size=15)),
                    ft.ChartAxisLabel(value=6, label=ft.Text("24h ago", size=15)),
                    ft.ChartAxisLabel(value=8, label=ft.Text("12h ago", size=15)),
                    ft.ChartAxisLabel(value=10, label=ft.Text("Now", size=15)),
                ],
                labels_size=30,
            ),
            left_axis=ft.ChartAxis(
                labels=[
                    ft.ChartAxisLabel(value=0, label=ft.Text("0", size=15)),
                    ft.ChartAxisLabel(
                        value=int(max_y / 2),
                        label=ft.Text(str(int(max_y / 2)), size=15),
                    ),
                    ft.ChartAxisLabel(value=max_y, label=ft.Text(str(max_y), size=15)),
                ],
                labels_size=30,
            ),
            border=ft.border.all(3, ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE)),
            tooltip_bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLUE_GREY_800),
            horizontal_grid_lines=ft.ChartGridLines(
                interval=max_y / 4,
                color=ft.Colors.with_opacity(0.2, ft.Colors.ON_SURFACE),
                width=1,
            ),
            vertical_grid_lines=ft.ChartGridLines(
                interval=1,
                color=ft.Colors.with_opacity(0.2, ft.Colors.ON_SURFACE),
                width=1,
            ),
            min_y=0,
            max_y=max_y,
            expand=True,
        )

        self.content = ft.Column(
            [
                ft.Text(
                    "Order Activity (Last 3 Days)", size=16, weight=ft.FontWeight.BOLD
                ),
                ft.Container(content=self.chart, height=300),
            ]
        )


class RightPanel(ft.Column):
    def __init__(self, content_controls=[]):
        super().__init__()

        self.col = {"sm": 10.5, "md": 10.5, "xl": 10.5}
        self.controls = [
            ft.Container(
                content=ft.Column(spacing=0, controls=content_controls),
                bgcolor=ft.Colors.TRANSPARENT,
                padding=ft.padding.only(20, 10, 20, 0),
            )
        ]


class DashboardPanel(RightPanel):
    def __init__(self):
        self.title = ft.Container(
            content=ft.ResponsiveRow(
                controls=[
                    ft.Text(
                        value="Bot Overview",
                        size=30,
                        weight=ft.FontWeight.BOLD,
                        col={"sm": 12, "md": 12, "xl": 12},
                    )
                ],
            ),
            padding=ft.padding.only(0, 0, 0, 10),
        )

        self.overview_panel = OverviewPanel()
        self.orders_graph = OrdersGraph()
        super().__init__(
            content_controls=[
                self.title,
                ft.Divider(),
                self.overview_panel,
                ft.Divider(),
                self.orders_graph,
            ]
        )


class BotControlPanel_REF(ft.Container):
    CITIES = [
        "Fort Sterling",
        "Lymhurst",
        "Bridgewatch",
        "Martlock",
        "Thetford",
        "Brecilien",
        "Caerleon",
        "Blackmarket",
    ]

    COMMAND_TYPES = [
        {
            "id": "travel_to",
            "label": "Travel to",
            "icon": ft.Icons.NAVIGATION_ROUNDED,
            "color": ft.Colors.BLUE_500,
        },
        {
            "id": "price_check",
            "label": "Price Check",
            "icon": ft.Icons.SEARCH_ROUNDED,
            "color": ft.Colors.PURPLE_500,
        },
        {
            "id": "buy_items",
            "label": "Buy items",
            "icon": ft.Icons.SHOPPING_CART_ROUNDED,
            "color": ft.Colors.GREEN_500,
        },
        {
            "id": "remove_orders",
            "label": "Remove orders",
            "icon": ft.Icons.CANCEL_ROUNDED,
            "color": ft.Colors.RED_500,
        },
        {
            "id": "wait_time",
            "label": "Wait time",
            "icon": ft.Icons.TIMER_OUTLINED,
            "color": ft.Colors.AMBER_500,
        },
    ]

    def __init__(self):
        super().__init__()
        self.expand = True
        # Using Hex for precise "Slate" look
        self.bgcolor = "#0f172a"
        self.padding = 20

        # Internal State
        self.sequence_data = []
        self.is_running = False
        self.current_execution_index = -1
        self.loop_task = None

        # --- UI COMPONENTS ---

        # Island Name Input
        self.island_input = ft.TextField(
            value="Home Island",
            label="Start/End Island Name",
            label_style=ft.TextStyle(color="#94a3b8", size=12),
            text_size=14,
            width=250,
            height=45,
            border_color="#334155",
            focused_border_color=ft.Colors.BLUE_500,
            prefix_icon=ft.Icons.MAP_OUTLINED,
            content_padding=ft.padding.all(10),
        )

        # Sequence Column (The Scrolling Frame)
        self.sequence_column = ft.Column(
            spacing=10,
            scroll=ft.ScrollMode.ADAPTIVE,
            height=480,
        )

        # Status Display
        self.status_text = ft.Text(
            "Idle", size=14, weight=ft.FontWeight.BOLD, color="#94a3b8"
        )
        self.status_indicator = ft.Container(
            width=10, height=10, border_radius=5, bgcolor="#334155"
        )

        # Loop Controls
        self.loop_checkbox = ft.Switch(
            label="Loop infinitely", label_position=ft.LabelPosition.RIGHT
        )
        self.loop_wait_input = ft.TextField(
            value="5",
            width=60,
            height=35,
            text_size=12,
            text_align=ft.TextAlign.CENTER,
            border_color="#334155",
            visible=False,
        )

        # Main Action Button
        self.run_button = ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED),
                    ft.Text("RUN BOT", weight="bold", size=18),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.BLUE_600,
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
            height=60,
            on_click=self.toggle_bot,
        )

        self.content = self.build_layout()

    def build_layout(self):
        # Left Side Functions
        functions_list = ft.Column(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "FUNCTIONS AVAILABLE",
                                size=11,
                                weight="bold",
                                color="#94a3b8",
                                style=ft.TextStyle(letter_spacing=1.2),
                            ),
                            *[
                                self.create_function_button(cmd)
                                for cmd in COMMAND_TYPES
                            ],
                        ],
                        spacing=10,
                    ),
                    bgcolor="#1e293b",
                    padding=20,
                    border_radius=15,
                    border=ft.border.all(1, "#334155"),
                ),
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.INFO_OUTLINE, color=ft.Colors.BLUE_400, size=20
                            ),
                            ft.Text(
                                "Bot will automatically travel from and to specified island at start and end.",
                                size=12,
                                color="#bfdbfe",
                                expand=True,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    bgcolor="#1e3a8a33",  # Transparent Blue
                    padding=15,
                    border_radius=12,
                    border=ft.border.all(1, "#3b82f64d"),
                ),
            ],
            spacing=15,
            width=300,
        )

        # Right Side Execution
        execution_pane = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("Execution Sequence", size=18, weight="bold"),
                            self.island_input,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(color="#334155", height=1),
                    self.sequence_column,
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Row(
                                            [
                                                self.loop_checkbox,
                                                ft.Text(
                                                    "Wait (s):",
                                                    size=12,
                                                    color="#64748b",
                                                ),
                                                self.loop_wait_input,
                                            ],
                                            spacing=10,
                                        ),
                                        ft.Container(
                                            content=ft.Row(
                                                [
                                                    self.status_indicator,
                                                    ft.Text(
                                                        "Bot State:",
                                                        size=12,
                                                        color="#64748b",
                                                        weight="bold",
                                                    ),
                                                    self.status_text,
                                                ],
                                                spacing=10,
                                            ),
                                            bgcolor="#020617",
                                            padding=ft.padding.symmetric(15, 10),
                                            border_radius=10,
                                            border=ft.border.all(1, "#1e293b"),
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                self.run_button,
                            ],
                            spacing=20,
                        ),
                        padding=ft.padding.only(top=20),
                    ),
                ]
            ),
            bgcolor="#1e293b",
            padding=20,
            border_radius=15,
            border=ft.border.all(1, "#334155"),
            expand=True,
        )

        self.loop_checkbox.on_change = lambda e: self.toggle_loop_wait(e)

        return ft.Row(
            [functions_list, execution_pane],
            spacing=25,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

    def toggle_loop_wait(self, e):
        self.loop_wait_input.visible = self.loop_checkbox.value
        self.update()

    def create_function_button(self, cmd_type):
        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Icon(
                            cmd_type["icon"], color=ft.Colors.WHITE, size=18
                        ),
                        bgcolor=cmd_type["color"],
                        padding=8,
                        border_radius=8,
                    ),
                    ft.Text(
                        cmd_type["label"],
                        weight="medium",
                        expand=True,
                        color=ft.Colors.WHITE,
                    ),
                    ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, color="#64748b", size=18),
                ]
            ),
            padding=10,
            border_radius=10,
            bgcolor="#334155",
            on_hover=self.on_btn_hover,
            on_click=lambda _: self.add_to_sequence(cmd_type),
        )

    def on_btn_hover(self, e):
        e.control.bgcolor = "#475569" if e.data == "true" else "#334155"
        e.control.update()

    def add_to_sequence(self, cmd_type):
        if self.is_running:
            return

        item_id = str(uuid.uuid4())
        new_item = {
            "uuid": item_id,
            "id": cmd_type["id"],
            "label": cmd_type["label"],
            "icon": cmd_type["icon"],
            "color": cmd_type["color"],
            "target_type": "market",
            "city": CITIES[0],
            "custom_island": "",
            "seconds": 5,
        }
        self.sequence_data.append(new_item)
        self.refresh_sequence_ui()

    def refresh_sequence_ui(self):
        self.sequence_column.controls.clear()

        # 1. Initial Travel Placeholder
        self.sequence_column.controls.append(self.build_auto_travel_row(is_start=True))

        # 2. Dynamic Sequence
        for idx, item in enumerate(self.sequence_data):
            self.sequence_column.controls.append(self.build_command_row(item, idx))

        # 3. Return Travel Placeholder
        self.sequence_column.controls.append(self.build_auto_travel_row(is_start=False))

        self.update()

    def build_auto_travel_row(self, is_start):
        active = self.current_execution_index == (-2 if is_start else -3)
        text = f"Auto-Travel {'From' if is_start else 'To'}: {self.island_input.value}"

        border_color = ft.Colors.BLUE_500 if active else "#334155"
        bg_color = "#1e3a8a33" if active else "#0f172a33"

        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(
                        ft.Icons.NAVIGATION_ROUNDED, color=ft.Colors.BLUE_400, size=16
                    ),
                    ft.Text(
                        text,
                        italic=True,
                        size=13,
                        color="#94a3b8" if not active else ft.Colors.WHITE,
                    ),
                ]
            ),
            padding=12,
            border_radius=10,
            border=ft.border.all(1, border_color),
            bgcolor=bg_color,
            opacity=1.0 if active else 0.5,
        )

    def build_command_row(self, item, idx):
        is_active = self.current_execution_index == idx
        config_controls = []

        if item["id"] == "travel_to":

            def on_type_change(e, uid=item["uuid"]):
                for i in self.sequence_data:
                    if i["uuid"] == uid:
                        i["target_type"] = e.control.value
                self.refresh_sequence_ui()

            type_dropdown = ft.Dropdown(
                value=item["target_type"],
                options=[ft.dropdown.Option("market"), ft.dropdown.Option("island")],
                width=100,
                height=35,
                text_size=11,
                border_color="#475569",
                on_change=on_type_change,
                disabled=self.is_running,
                content_padding=ft.padding.symmetric(0, 5),
            )
            config_controls.append(type_dropdown)

            if item["target_type"] == "market":

                def on_city_change(e, uid=item["uuid"]):
                    for i in self.sequence_data:
                        if i["uuid"] == uid:
                            i["city"] = e.control.value

                city_dropdown = ft.Dropdown(
                    value=item["city"],
                    options=[ft.dropdown.Option(c) for c in CITIES],
                    width=130,
                    height=35,
                    text_size=11,
                    border_color="#475569",
                    on_change=on_city_change,
                    disabled=self.is_running,
                    content_padding=ft.padding.symmetric(0, 5),
                )
                config_controls.append(city_dropdown)
            else:

                def on_island_change(e, uid=item["uuid"]):
                    for i in self.sequence_data:
                        if i["uuid"] == uid:
                            i["custom_island"] = e.control.value

                island_field = ft.TextField(
                    value=item["custom_island"],
                    hint_text="Island Name",
                    hint_style=ft.TextStyle(size=11),
                    width=130,
                    height=35,
                    text_size=11,
                    border_color="#475569",
                    on_change=on_island_change,
                    disabled=self.is_running,
                    content_padding=ft.padding.symmetric(0, 5),
                )
                config_controls.append(island_field)

        elif item["id"] == "wait_time":

            def on_wait_change(e, uid=item["uuid"]):
                try:
                    val = int(e.control.value or 0)
                    for i in self.sequence_data:
                        if i["uuid"] == uid:
                            i["seconds"] = val
                except ValueError:
                    pass

            wait_field = ft.TextField(
                value=str(item["seconds"]),
                width=60,
                height=35,
                text_size=11,
                border_color="#475569",
                on_change=on_wait_change,
                text_align=ft.TextAlign.CENTER,
                disabled=self.is_running,
                content_padding=ft.padding.symmetric(0, 5),
            )
            config_controls.extend(
                [wait_field, ft.Text("sec", size=10, color="#64748b")]
            )
        else:
            config_controls.append(
                ft.Text("Standard execution", size=10, italic=True, color="#64748b")
            )

        bg_color = "#3341554d" if not is_active else "#3b82f633"
        border_color = ft.Colors.BLUE_500 if is_active else "#334155"

        return ft.Container(
            content=ft.Row(
                [
                    ft.Text(f"{idx+1:02}", size=10, color="#64748b", width=20),
                    ft.Container(
                        ft.Icon(item["icon"], size=14, color=ft.Colors.WHITE),
                        bgcolor=item["color"],
                        padding=6,
                        border_radius=6,
                    ),
                    ft.Text(
                        item["label"],
                        weight="bold",
                        size=13,
                        width=90,
                        no_wrap=True,
                        color=ft.Colors.WHITE,
                    ),
                    ft.VerticalDivider(color="#334155", width=1),
                    ft.Row(config_controls, spacing=10, expand=True),
                    ft.Row(
                        [
                            ft.IconButton(
                                ft.Icons.KEYBOARD_ARROW_UP,
                                icon_size=16,
                                on_click=lambda _: self.move_item(idx, -1),
                                disabled=self.is_running or idx == 0,
                            ),
                            ft.IconButton(
                                ft.Icons.KEYBOARD_ARROW_DOWN,
                                icon_size=16,
                                on_click=lambda _: self.move_item(idx, 1),
                                disabled=self.is_running
                                or idx == len(self.sequence_data) - 1,
                            ),
                            ft.IconButton(
                                ft.Icons.DELETE_OUTLINE,
                                icon_size=16,
                                icon_color=ft.Colors.RED_300,
                                on_click=lambda _: self.remove_item(idx),
                                disabled=self.is_running,
                            ),
                        ],
                        spacing=0,
                    ),
                ],
                spacing=10,
            ),
            padding=ft.padding.symmetric(5, 12),
            border_radius=10,
            bgcolor=bg_color,
            border=ft.border.all(1, border_color),
        )

    def move_item(self, index, direction):
        target = index + direction
        self.sequence_data[index], self.sequence_data[target] = (
            self.sequence_data[target],
            self.sequence_data[index],
        )
        self.refresh_sequence_ui()

    def remove_item(self, index):
        self.sequence_data.pop(index)
        self.refresh_sequence_ui()

    def toggle_bot(self, _):
        if self.is_running:
            self.stop_bot()
        else:
            self.start_bot()

    def start_bot(self):
        if not self.sequence_data:
            return
        self.is_running = True
        self.run_button.bgcolor = ft.Colors.RED_600
        self.run_button.content.controls[0].name = ft.Icons.SQUARE_ROUNDED
        self.run_button.content.controls[1].value = "STOP BOT"
        self.status_indicator.bgcolor = ft.Colors.GREEN_500
        self.refresh_sequence_ui()
        self.loop_task = asyncio.create_task(self.execution_loop())

    def stop_bot(self):
        self.is_running = False
        if self.loop_task:
            self.loop_task.cancel()
        self.run_button.bgcolor = ft.Colors.BLUE_600
        self.run_button.content.controls[0].name = ft.Icons.PLAY_ARROW_ROUNDED
        self.run_button.content.controls[1].value = "RUN BOT"
        self.status_indicator.bgcolor = "#334155"
        self.status_text.value = "Idle"
        self.status_text.color = "#94a3b8"
        self.current_execution_index = -1
        self.refresh_sequence_ui()

    async def execution_loop(self):
        try:
            while self.is_running:
                # 1. Travel FROM
                self.current_execution_index = -2
                self.status_text.value = f"Traveling from {self.island_input.value}..."
                self.status_text.color = ft.Colors.BLUE_400
                self.refresh_sequence_ui()
                await asyncio.sleep(2)

                # 2. Middle Sequence
                for i, cmd in enumerate(self.sequence_data):
                    if not self.is_running:
                        break
                    self.current_execution_index = i
                    label = cmd["label"]
                    duration = 1.5
                    if cmd["id"] == "travel_to":
                        dest = (
                            cmd["city"]
                            if cmd["target_type"] == "market"
                            else cmd["custom_island"]
                        )
                        label = f"Traveling to {dest}..."
                    elif cmd["id"] == "wait_time":
                        label = f"Waiting {cmd['seconds']}s..."
                        duration = cmd["seconds"]
                    self.status_text.value = label
                    self.refresh_sequence_ui()
                    await asyncio.sleep(duration)

                # 3. Return TO
                if self.is_running:
                    self.current_execution_index = -3
                    self.status_text.value = (
                        f"Returning to {self.island_input.value}..."
                    )
                    self.refresh_sequence_ui()
                    await asyncio.sleep(2)

                if self.loop_checkbox.value and self.is_running:
                    self.current_execution_index = -1
                    wait_time = int(self.loop_wait_input.value or 0)
                    self.status_text.value = f"Loop pause: {wait_time}s"
                    self.refresh_sequence_ui()
                    await asyncio.sleep(wait_time)
                else:
                    break
            self.stop_bot()
        except asyncio.CancelledError:
            pass


class BotExecutionWarning(ft.Container):
    def __init__(self):
        super().__init__()
        self.content = ft.Row(
            controls=[
                ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.BLUE_400, size=20, offset=ft.Offset(0, 0.1)),
                ft.Text(
                    "Bot will automatically travel from and to specified island at start and end.",
                    size=16,
                    color="#bfdbfe",
                    expand=True,
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
        self.bgcolor = "#3272a0ff"
        self.padding = 15
        self.border_radius = 12
        self.border = ft.border.all(1, "#bdbcb9ff")


class AddSequenceFunctionButton(ft.ElevatedButton):
    COMMAND_TYPES = {
        "travel_to": {
            "label": "Travel to",
            "icon": ft.Icons.NAVIGATION_ROUNDED,
            "color": ft.Colors.BLUE_500,
        },
        "price_check": {
            "label": "Price Check",
            "icon": ft.Icons.SEARCH_ROUNDED,
            "color": ft.Colors.PURPLE_500,
        },
        "buy_items": {
            "label": "Buy items",
            "icon": ft.Icons.SHOPPING_CART_ROUNDED,
            "color": "#0d9259",
        },
        "remove_orders": {
            "label": "Remove orders",
            "icon": ft.Icons.CANCEL_ROUNDED,
            "color": "#b02d21",
        },
        "wait_time": {
            "label": "Wait time",
            "icon": ft.Icons.TIMER_OUTLINED,
            "color": "#cd9316",
        },
    }

    def __init__(self, cmd_id: str):
        super().__init__()
        self.style = ft.ButtonStyle(
            padding=ft.padding.only(10, 15, 10, 15),
            bgcolor="#255b85",
            shape=ft.RoundedRectangleBorder(radius=10),
        )
        self.content = ft.Row(
            [
                ft.Container(
                    content=ft.Icon(
                        self.COMMAND_TYPES[cmd_id]["icon"],
                        color=ft.Colors.WHITE,
                        size=18,
                    ),
                    bgcolor=self.COMMAND_TYPES[cmd_id]["color"],
                    padding=8,
                    border_radius=8,
                ),
                ft.Text(
                    self.COMMAND_TYPES[cmd_id]["label"],
                    weight="medium",
                    expand=True,
                    color=ft.Colors.WHITE,
                ),
                ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, color="#e4e4e4", size=18),
            ]
        )


class FunctionsAvaliablePanel(ft.Container):
    def __init__(self):
        super().__init__()
        self.title = ft.Text(
            value="FUNCTIONS AVAILABLE",
            size=15,
            weight="bold",
            color="#94a3b8",
            style=ft.TextStyle(letter_spacing=1.2),
            width=float("inf"),
        )
        self.bgcolor = "#1e293b"
        self.padding = ft.padding.only(20, 15, 20, 20)
        self.border_radius = 15
        self.border = ft.border.all(1, "#334155")

        self.travel_to_button = AddSequenceFunctionButton("travel_to")
        self.price_check_button = AddSequenceFunctionButton("price_check")
        self.buy_items_button = AddSequenceFunctionButton("buy_items")
        self.remove_orders_button = AddSequenceFunctionButton("remove_orders")
        self.wait_time_button = AddSequenceFunctionButton("wait_time")

        self.content = ft.Column(
            controls=[
                self.title,
                self.travel_to_button,
                self.price_check_button,
                self.buy_items_button,
                self.remove_orders_button,
                self.wait_time_button,
            ]
        )


class ExecutionFunctionsList(ft.Container):
    def __init__(self):
        super().__init__()
        


class ExecutionSequencePanel(ft.Container):
    def __init__(self):
        super().__init__()

        title = ft.Text(
            value="Execution Sequence", 
            weight="bold", 
            size=25,
            col=8,
            offset=ft.Offset(0, .1)
        )
        self.home_island = ft.TextField(
            label="Start/End Island Name",
            text_size=12,
            col=4,
            prefix_icon=ft.Icons.MAP_OUTLINED,
        )

        self.bgcolor = "#1e293b"
        self.padding = ft.padding.only(20, 15, 20, 20)
        self.border_radius = 15
        self.border = ft.border.all(1, "#334155")
        self.content = ft.Column(
            controls=[
                ft.ResponsiveRow(
                    controls=[
                        title,
                        self.home_island,
                    ],
                    vertical_alignment=ft.VerticalAlignment.CENTER
                ),
                ft.Divider(),
                ExecutionFunctionsList(),
            ],
            width=float("inf")
        )


class BotControlPanel(ft.Container):
    def __init__(self):
        super().__init__()
        left_side_size = 3
        self.padding = ft.padding.only(0, 10, 0, 0)

        self.functions_avaliable_panel = FunctionsAvaliablePanel()
        self.execution_warning = BotExecutionWarning()
        self.execution_sequence_panel = ExecutionSequencePanel()

        self.content = ft.ResponsiveRow(
            controls=[
                ft.Column(
                    controls=[self.functions_avaliable_panel, self.execution_warning],
                    col={
                        "sm": left_side_size,
                        "md": left_side_size,
                        "xl": left_side_size,
                    },
                ),
                ft.Column(
                    controls=[self.execution_sequence_panel],
                    col={
                        "sm": 12 - left_side_size,
                        "md": 12 - left_side_size,
                        "xl": 12 - left_side_size,
                    },
                ),
            ]
        )


class BotSequencePanel(RightPanel):
    def __init__(self):
        self.title = ft.Container(
            content=ft.ResponsiveRow(
                controls=[
                    ft.Text(
                        value="Configure Bot Sequence",
                        size=30,
                        weight=ft.FontWeight.BOLD,
                        col={"sm": 12, "md": 12, "xl": 12},
                    )
                ],
            ),
            padding=ft.padding.only(0, 0, 0, 10),
        )

        super().__init__(
            content_controls=[
                self.title,
                ft.Divider(),
                BotControlPanel(),
            ]
        )


class ActivityLogsPanel(RightPanel):
    def __init__(self):
        self.title = ft.Container(
            content=ft.ResponsiveRow(
                controls=[
                    ft.Text(
                        value="Bot Activity Logs",
                        size=30,
                        weight=ft.FontWeight.BOLD,
                        col={"sm": 12, "md": 12, "xl": 12},
                    )
                ],
            ),
            padding=ft.padding.only(0, 0, 0, 10),
        )

        super().__init__(content_controls=[self.title])


class Dashboard(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.dashboard_panel = DashboardPanel()
        self.bot_sequence_panel = BotSequencePanel()
        self.bot_activity_panel = ActivityLogsPanel()
        self.left_panel = LeftPanel()

        self.left_panel.dashboard_button.on_click = self.change_tab
        self.left_panel.sequence_button.on_click = self.change_tab
        self.left_panel.logs_button.on_click = self.change_tab

        self.right_panels = {
            "dashboard": self.dashboard_panel,
            "sequence": self.bot_sequence_panel,
            "logs": self.bot_activity_panel,
        }

        self.content = ft.ResponsiveRow(
            controls=[self.left_panel, self.bot_sequence_panel], spacing=0
        )

    def change_tab(self, event):
        self.content = ft.ResponsiveRow(
            controls=[self.left_panel, self.right_panels[event.control.data]], spacing=0
        )
        self.update()

        # ADD HERE LOGIC TO UPDATE DATA


def main(page: ft.Page):
    page.padding = 0
    page.title = "Dashboard"
    page.expand = True

    dashboard = Dashboard()

    page.add(dashboard)
    # dashboard.dashboard_panel.overview_panel.subscribed_until.update_data("Data Updated")
    page.update()


if __name__ == "__main__":
    ft.app(target=main)
