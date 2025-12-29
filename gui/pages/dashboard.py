import flet as ft
import threading
import time
import keyboard
from components import BotOverlay
from bot import Bot


COMMAND_TYPES = {
    "travel_to": {
        "label": "Travel to",
        "icon": ft.Icons.NAVIGATION_ROUNDED,
        "color": ft.Colors.BLUE_500,
        "func": "travel_to" # Placeholder
    },
    "price_check": {
        "label": "Price Check",
        "icon": ft.Icons.SEARCH_ROUNDED,
        "color": ft.Colors.PURPLE_500,
        "func": "check_price"
    },
    "buy_items": {
        "label": "Buy items",
        "icon": ft.Icons.SHOPPING_CART_ROUNDED,
        "color": "#0d9259",
        "func": "buy_items"
    },
    "remove_orders": {
        "label": "Remove orders",
        "icon": ft.Icons.CANCEL_ROUNDED,
        "color": "#b02d21",
        "func": "remove_orders"
    },
    "wait_time": {
        "label": "Wait time",
        "icon": ft.Icons.TIMER_OUTLINED,
        "color": "#cd9316",
        "func": "wait_time" # Placeholder
    },
}


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
    def __init__(self, content_controls=[], scroll_mode: ft.ScrollMode | None = ft.ScrollMode.AUTO):
        super().__init__()
        self.scroll = scroll_mode
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
    def __init__(self, cmd_id: str):
        super().__init__()
        self.data = cmd_id
        self.style = ft.ButtonStyle(
            padding=ft.padding.only(10, 15, 10, 15),
            bgcolor="#255b85",
            shape=ft.RoundedRectangleBorder(radius=10),
        )
        self.content = ft.Row(
            [
                ft.Container(
                    content=ft.Icon(
                        COMMAND_TYPES[cmd_id]["icon"],
                        color=ft.Colors.WHITE,
                        size=18,
                    ),
                    bgcolor=COMMAND_TYPES[cmd_id]["color"],
                    padding=8,
                    border_radius=8,
                ),
                ft.Text(
                    COMMAND_TYPES[cmd_id]["label"],
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

        self.buttons = {
            "travel_to": self.travel_to_button,
            "price_check": self.price_check_button,
            "buy_items": self.buy_items_button,
            "remove_orders": self.remove_orders_button,
            "wait_time": self.wait_time_button,
        }

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


class TravelToAdditionalInfo(ft.Container):
    def __init__(self, initial_data=None, on_change_callback=None):
        super().__init__()
        self.col={"sm": 7, "md": 7, "xl": 7}
        self.on_change_callback = on_change_callback
        
        dest_val = initial_data.get("destination", "market") if initial_data else "market"
        market_val = initial_data.get("market_city", "black_market") if initial_data else "black_market"
        island_val = initial_data.get("island_name", "") if initial_data else ""

        self.destination_type = ft.Container(
            content=ft.Dropdown(
                expand=True,
                value=dest_val,
                label="Destination",
                options=[
                    ft.DropdownOption(key="market", text="Market"),
                    ft.DropdownOption(key="island", text="Island")
                ],
                on_change=self.on_destination_type_change,
            ),
            col={"sm": 5, "md": 5, "xl": 4},
        )

        self.market_name = ft.Container(
            content=ft.Dropdown(
                expand=True,
                value=market_val,
                label="Market City",
                options=[
                    ft.DropdownOption(key="black_market", text="Black Market"),
                    ft.DropdownOption(key="fort_sterling", text="Fort Sterling"),
                    ft.DropdownOption(key="lymhurst", text="Lymhurst"),
                    ft.DropdownOption(key="bridgewatch", text="Bridgewatch"),
                    ft.DropdownOption(key="martlock", text="Martlock"),
                    ft.DropdownOption(key="thetford", text="Thetford"),
                    ft.DropdownOption(key="caerleon", text="Caerleon"),
                    ft.DropdownOption(key="brecilien", text="Brecilien"),
                ],
                on_change=lambda _: self.trigger_save()
            ),
            col={"sm": 7, "md": 7, "xl": 7},
            visible=(dest_val == "market")
        )

        self.island_name = ft.Container(
            content=ft.TextField(
                expand=True,
                value=island_val,
                label="Island Name",
                on_change=lambda _: self.trigger_save()
            ),
            col={"sm": 7, "md": 7, "xl": 7},
            visible=(dest_val == "island")
        )

        self.content = ft.ResponsiveRow(
            controls=[self.destination_type, self.market_name, self.island_name]
        )

    def trigger_save(self):
        if self.on_change_callback:
            self.on_change_callback()

    def on_destination_type_change(self, event):
        is_market = self.destination_type.content.value == "market"
        self.market_name.visible = is_market
        self.island_name.visible = not is_market
        self.update()
        self.trigger_save()

    def get_data(self):
        return {
            "destination": self.destination_type.content.value,
            "market_city": self.market_name.content.value,
            "island_name": self.island_name.content.value
        }


class WaitTimeAdditionalInfo(ft.Container):
    def __init__(self, initial_data=None, on_change_callback=None):
        super().__init__()
        self.col={"sm": 7, "md": 7, "xl": 7}
        self.on_change_callback = on_change_callback
        val = initial_data.get("minutes", "5") if initial_data else "5"

        self.wait_time_amount = ft.Container(
            content=ft.TextField(
                expand=True,
                value=val,
                label="Minutes",
                on_change=lambda _: self.trigger_save()
            ),
            col={"sm": 7, "md": 7, "xl": 7},
        )
        self.content = ft.ResponsiveRow(controls=[self.wait_time_amount])

    def trigger_save(self):
        if self.on_change_callback:
            self.on_change_callback()

    def get_data(self):
        return {"minutes": self.wait_time_amount.content.value}


class FunctionToExecute(ft.Container):
    def __init__(self, function_type: str, can_be_removed: bool = False, initial_data=None, on_change_callback=None):
        super().__init__()
        self.function_type = function_type
        self.index = ft.Container(content=ft.Text("0"), col={"sm": .6}, alignment=ft.alignment.center)
        self.title = ft.Text(COMMAND_TYPES[function_type]["label"], size=18, weight="bold", col={"sm": 3})
        self.icon = ft.Container(
            col={"sm": .7}, aspect_ratio=1, bgcolor=COMMAND_TYPES[function_type]["color"],
            border_radius=4, alignment=ft.alignment.center,
            content=ft.Icon(name=COMMAND_TYPES[function_type]["icon"], color="#ffffff"),
        )
        
        remove_btn_container = ft.Container(
            content=ft.IconButton(icon=ft.Icons.DELETE, icon_color="#b32525"),
            col={"sm": 1}, alignment=ft.alignment.center_right
        )
        self.remove_button = remove_btn_container.content

        self.additional_info = ft.Container(col=0)
        if function_type == "travel_to":
            self.additional_info = TravelToAdditionalInfo(initial_data, on_change_callback)
        elif function_type == "wait_time":
            self.additional_info = WaitTimeAdditionalInfo(initial_data, on_change_callback)

        self.padding = 10
        self.bgcolor = "#2D3A55"
        self.border_radius = 8
        self.content = ft.ResponsiveRow(
            controls=[
                ft.ResponsiveRow(
                    controls=[self.index, self.icon, self.title, self.additional_info],
                    spacing=20, vertical_alignment=ft.CrossAxisAlignment.CENTER, col={"sm": 10}
                ),
                remove_btn_container if can_be_removed else ft.Container(col=1)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

    def get_serialized_data(self):
        data = {"type": self.function_type}
        if hasattr(self.additional_info, "get_data"):
            data["data"] = self.additional_info.get_data()
        return data


class ExecutionFunctionsList(ft.Container):
    def __init__(self, dashboard):
        super().__init__()
        self.dashboard = dashboard
        self.height = 400
        initial_move_to = FunctionToExecute("travel_to", can_be_removed=False)
        
        self.content = ft.Column(
            controls=[initial_move_to],
            scroll=ft.ScrollMode.AUTO,
        )
        self.update_indexes()

    def load_sequence(self, sequence_data):
        self.content.controls.clear()
        for i, item in enumerate(sequence_data):
            func_type = item.get("type", "price_check")
            new_func = FunctionToExecute(
                func_type, 
                can_be_removed=False if i == 0 else True, 
                initial_data=item.get("data"),
                on_change_callback=self.dashboard.save_sequence
            )
            self.content.controls.append(new_func)
        
        self.update_indexes()

    def add_function(self, event):
        new_function = FunctionToExecute(
            event.control.data, 
            can_be_removed=True,
            on_change_callback=self.dashboard.save_sequence
        )
        self.content.controls.append(new_function)
        self.update_indexes()
        self.dashboard.save_sequence()

    def remove_function(self, e: ft.ControlEvent):
        try:
            function_index = int(e.control.data)
            if 0 <= function_index < len(self.content.controls):
                self.content.controls.pop(function_index)
                self.update_indexes()
                self.dashboard.save_sequence()
        except (ValueError, TypeError):
            pass

    def update_indexes(self):
        for i, function in enumerate(self.content.controls):
            function.index.content.value = str(i)
            function.remove_button.data = str(i)
            function.remove_button.on_click = self.remove_function
            
        if self.page: 
            self.update()


class ExecutionSequencePanel(ft.Container):
    def __init__(self, dashboard):
        super().__init__()
        self.dashboard = dashboard

        self.execution_functions_list = ExecutionFunctionsList(dashboard=dashboard)
        self.loop_checkbox = ft.Switch(
            value=False,
            label="Loop infinitely",
            label_position=ft.LabelPosition.RIGHT,
            col={"sm": 6, "md": 3, "xl": 3},
            on_change=self.loop_toggle
        )
        self.status_text = ft.Text(
            "Idle", size=14, weight=ft.FontWeight.BOLD, color="#94a3b8"
        )
        self.status_indicator = ft.Container(
            width=10, height=10, border_radius=5, bgcolor="#334155"
        )

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

        self.wait_before_loop = ft.TextField(
            label="Wait before repeat (minutes)",
            col={"sm": 6, "md": 5, "xl": 6},
            visible=False
        )

        self.bot_status = ft.Container(
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
            col={"sm": 4, "md": 4, "xl": 4}
        )

        self.lower_row = ft.ResponsiveRow(
            controls=[
                ft.ResponsiveRow(
                    controls=[
                        self.loop_checkbox,
                        self.wait_before_loop,
                    ],
                    col={"sm": 8, "md": 8, "xl": 8}
                ),
                ft.Column(
                    controls=[
                        self.bot_status,
                    ],
                    col={"sm": 4, "md": 4, "xl": 4}
                ), 
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self.run_button = ft.ElevatedButton(
            content=ft.Row(
                [ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED), ft.Text("RUN BOT", weight="bold", size=18)],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.BLUE_600,
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            height=45,
            col={"sm": 5, "md": 3.5, "xl": 2.45},
            on_click=self.bot_toggle,
            data="run"
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
                self.execution_functions_list,
                ft.Divider(),
                ft.Container(content=self.lower_row, padding=ft.padding.only(0, 0, 0, 10)),
                ft.ResponsiveRow(
                    controls=[
                        self.run_button
                    ],
                    alignment=ft.MainAxisAlignment.END
                )
            ],
            width=float("inf")
        )

    def bot_toggle(self, e):
        self.run_button.disabled = True
        self.run_button.content=ft.Row(
            [ft.Icon(ft.Icons.PAUSE_ROUNDED), ft.Text("STARTING", weight="bold", size=18)],
            alignment=ft.MainAxisAlignment.CENTER,
        )
        self.run_button.style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor="#312e2e",
            shape=ft.RoundedRectangleBorder(radius=8),
        )
        self.run_button.update()
            
        if self.run_button.data == "run":
            if self.dashboard.bot != None:
                self.dashboard.bot.destroy()
            self.dashboard.bot = Bot()
            self.dashboard.app.bot = self.dashboard.bot
            self.run_button.content=ft.Row(
                [ft.Icon(ft.Icons.PAUSE_ROUNDED), ft.Text("STOP", weight="bold", size=18)],
                alignment=ft.MainAxisAlignment.CENTER,
            )
            self.run_button.style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.RED_600,
                shape=ft.RoundedRectangleBorder(radius=8),
            )
            self.dashboard.start_sequence()
            self.run_button.data = "stop"
            self.run_button.disabled = False
        elif self.run_button.data == "stop":
            self.dashboard.bot.destroy()
            self.run_button.content=ft.Row(
                [ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED), ft.Text("RUN BOT", weight="bold", size=18)],
                alignment=ft.MainAxisAlignment.CENTER,
            )
            self.run_button.style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.BLUE_600,
                shape=ft.RoundedRectangleBorder(radius=8),
            )
            if self.dashboard.bot.status == "Running":
                self.dashboard.bot.toggle_pause()
                time.sleep(1)
            self.dashboard.stop_sequence()
            self.run_button.data = "run"
            self.run_button.disabled = False

        self.run_button.update()

    def loop_toggle(self, e):
        if self.loop_checkbox.value:
            self.wait_before_loop.visible = True
        else:
            self.wait_before_loop.visible = False
        self.dashboard.loop_sequence = self.loop_checkbox.value
        
        self.update()

    def update_status(self, text: str, color: str):
        self.status_text.value = text
        self.status_indicator.bgcolor = color
        if self.page: self.update()


class BotControlPanel(ft.Container):
    def __init__(self, dashboard):
        super().__init__()
        left_side_size = 3
        self.padding = ft.padding.only(0, 10, 0, 0)

        self.execution_warning = BotExecutionWarning()
        self.execution_sequence_panel = ExecutionSequencePanel(dashboard)
        self.functions_avaliable_panel = FunctionsAvaliablePanel()

        for key in self.functions_avaliable_panel.buttons:
            execution_list =self.execution_sequence_panel.execution_functions_list
            self.functions_avaliable_panel.buttons[key].on_click = execution_list.add_function

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
    def __init__(self, dashboard):
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

        self.bot_control_panel = BotControlPanel(dashboard=dashboard)

        super().__init__(
            content_controls=[
                self.title,
                ft.Divider(),
                self.bot_control_panel,
            ]
        )


class ActivityLogItem(ft.Container):
    def __init__(self, title: str, on_click=None):
        super().__init__()
        self.title = ft.Text(
            value=title,
            weight="bold",
            size=22,
            color="#ffffff",
            col={"sm": 12, "md": 12, "xl": 12}
        )

        self.content = ft.ElevatedButton(
            content=ft.ResponsiveRow(
                controls=[self.title]
            ),
            style=ft.ButtonStyle(
                padding=ft.padding.only(20, 20, 20, 20),
                bgcolor="#415E7A",
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=on_click # Added on_click handler
        )


class LogsView(ft.Container):
    LOG_COLORS = {
        "system": ft.Colors.BLUE_400,
        "activity": ft.Colors.GREEN_400,
        "orders": ft.Colors.AMBER_500,
        "error": ft.Colors.RED_400
    }

    class LogRow(ft.Row):
        def __init__(self, category: str, message: str, color: str):
            super().__init__()
            self.vertical_alignment = ft.CrossAxisAlignment.START
            self.controls = [
                ft.Container(
                    content=ft.Text(category.upper(), size=10, weight="bold", color=ft.Colors.BLACK),
                    bgcolor=color,
                    padding=ft.padding.symmetric(horizontal=5, vertical=2),
                    border_radius=3,
                    width=70,
                    alignment=ft.alignment.center,
                ),
                ft.Text(message, size=13, font_family="monospace", expand=True)
            ]

    def __init__(self, initial_logs=None):
        super().__init__()
        self.padding = 10
        self.border = ft.border.all(1, ft.Colors.OUTLINE_VARIANT)
        self.border_radius = 8
        self.bgcolor = ft.Colors.BLACK12
        self.expand = True

        self.log_column = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=5,
            auto_scroll=True
        )
        
        self.content = self.log_column

        if initial_logs:
            for entry in initial_logs:
                if ";" in entry:
                    category, message = entry.split(";", 1)
                    color = self.LOG_COLORS.get(category.lower(), ft.Colors.GREY_400)
                    self.log_column.controls.append(
                        self.LogRow(category, message, color)
                    )

    def add_logs(self, log_list: list[str]):
        for entry in log_list:
            if ";" in entry:
                category, message = entry.split(";", 1)
                color = self.LOG_COLORS.get(category.lower(), ft.Colors.GREY_400)
                self.log_column.controls.append(
                    self.LogRow(category, message, color)
                )
        self.update()


class ActivityLogsPanel(RightPanel):
    def __init__(self):
        super().__init__()
        self.expand = True

        self.back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
            icon_size=20,
            on_click=lambda _: self.show_logs_list(),
            visible=False,
            icon_color="#ffffff"
        )
        self.title_text = ft.Text(
            value="Bot Activity Logs",
            size=30,
            weight=ft.FontWeight.BOLD,
        )
        self.title_container = ft.Container(
            content=ft.Row(
                controls=[self.back_button, self.title_text],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.padding.only(0, 0, 0, 10),
        )

        self.logs_list_content = ft.Column(
            controls=[
                ActivityLogItem("23.12.2025 | 14:42 UTC | Current Session", on_click=self.handle_log_click),
                ActivityLogItem("23.12.2025 | 12:17 UTC", on_click=self.handle_log_click),
                ActivityLogItem("22.12.2025 | 10:17 UTC", on_click=self.handle_log_click),
            ],
            spacing=10
        )

        # 3. Content for Details State
        # In a real app, you would pass the actual data from the JSON file here
        self.logs_view = LogsView(
            initial_logs=[
                "system;Bot Initialized",
                "system;Database connected",
                "system;Items loaded (1972)",
                "activity;Started to make orders",
                "orders;Order Made | Novice's Scholar Robe | BM: 1920 | Order: 54 | Amount: 12",
                "orders;Order Made | Novice's Scholar Jacket | BM: 162 | Order: 2 | Amount: 120",
                "orders;Order Made | Novice's Scholar Shoes | BM: 5245 | Order: 554 | Amount: 8",
            ]
        )
        self.logs_view.visible = False
        self.logs_view.margin = ft.margin.only(0, 10, 0, 20)

        self.inner_column = self.controls[0].content 
        
        self._setup_initial_view()

    def _setup_initial_view(self):
        self.scroll = ft.ScrollMode.AUTO
        self.back_button.visible = False
        self.title_text.value = "Bot Activity Logs"
        self.logs_list_content.visible = True
        self.logs_view.visible = False
        self.logs_view.expand = False

        self.inner_column.controls = [
            self.title_container,
            ft.Divider(),
            self.logs_list_content
        ]

    def handle_log_click(self, e):
        self.show_log_details()

    def show_logs_list(self):
        self.scroll = ft.ScrollMode.AUTO
        self.back_button.visible = False
        self.title_text.value = "Bot Activity Logs"
        
        self.logs_list_content.visible = True
        self.logs_view.visible = False
        self.logs_view.expand = False

        self.inner_column.controls = [
            self.title_container,
            ft.Divider(),
            self.logs_list_content
        ]
        self.update()

    def show_log_details(self):
        self.scroll = None
        self.back_button.visible = True
        self.title_text.value = "Session Details"

        self.logs_list_content.visible = False
        self.logs_view.visible = True
        self.logs_view.expand = True

        self.controls[0].expand = True
        self.inner_column.expand = True

        self.inner_column.controls = [
            self.title_container,
            ft.Divider(),
            self.logs_view
        ]

        if self.page:
            self.update()


class Dashboard(ft.Container):
    bot: Bot | None
    def __init__(self, app=None, config=None, page=None, bot: Bot = None, header=None):
        super().__init__()
        self.expand = True
        self.app = app
        self.config = config
        self.page = page
        self.bot = bot
        self.header = header

        self.app.overlay = None
        self.is_running_sequence = False
        self.loop_sequence = False
        self.bot_sequence = self.config.load_bot_loop() if self.config else []

        self.dashboard_panel = DashboardPanel()
        self.bot_sequence_panel = BotSequencePanel(dashboard=self)
        self.bot_activity_panel = ActivityLogsPanel()
        self.left_panel = LeftPanel()

        self.seq_panel = self.bot_sequence_panel.bot_control_panel.execution_sequence_panel
        self.avail_panel = self.bot_sequence_panel.bot_control_panel.functions_avaliable_panel

        self.seq_panel.execution_functions_list.load_sequence(self.bot_sequence)

        self.left_panel.dashboard_button.on_click = self.change_tab
        self.left_panel.sequence_button.on_click = self.change_tab
        self.left_panel.logs_button.on_click = self.change_tab

        self.right_panels = {
            "dashboard": self.dashboard_panel,
            "sequence": self.bot_sequence_panel,
            "logs": self.bot_activity_panel,
        }

        self.content = ft.ResponsiveRow(
            controls=[self.left_panel, self.dashboard_panel], spacing=0,
        )

        try:
            keyboard.remove_hotkey('ctrl+p')
        except:
            pass
        
        try:
            keyboard.add_hotkey('ctrl+p', lambda: self._on_global_hotkey())
        except Exception as e:
            print(f"Failed to register global hotkey: {e}")

    def set_ui_lock(self, locked: bool):
        self.seq_panel.home_island.disabled = locked
        self.seq_panel.loop_checkbox.disabled = locked
        self.seq_panel.wait_before_loop.disabled = locked
        self.avail_panel.disabled = locked
        self.seq_panel.execution_functions_list.disabled = locked
        
        self.update()

    def save_sequence(self):
        self.bot_sequence = [c.get_serialized_data() for c in self.seq_panel.execution_functions_list.content.controls]
        if self.config: 
            self.config.save_bot_loop(self.bot_sequence)

    def _on_global_hotkey(self):
        if self.bot:
            try:
                paused = self.bot.toggle_pause()
                if self.app.overlay:
                    self.app.overlay.send_update(
                        status="Paused" if paused else "Running", 
                        task=self.bot.current_task_name, 
                        paused=paused
                    )

                status = "PAUSED (Ctrl+P to Resume)" if paused else "Running"
                color = ft.Colors.ORANGE_400 if paused else ft.Colors.GREEN_400
                self.seq_panel.update_status(status, color)
            except Exception as e:
                print(f"Hotkey Error: {e}")

    def start_sequence(self):
        if not self.bot_sequence: return
        if self.app.bot == None:
            self.bot = Bot()
            self.app.bot = self.bot
        if self.app.overlay == None:
            self.app.overlay = BotOverlay()
        self.app.overlay.start()
        time.sleep(3)
        self.is_running_sequence = True
        self.set_ui_lock(True)
        self.seq_panel.update_status("Initializing...", ft.Colors.BLUE_400)

        threading.Thread(target=self.sequence_worker, daemon=True).start()

    def stop_sequence(self):
        self.is_running_sequence = False
        self.set_ui_lock(False)
        self.seq_panel.update_status("Stopped", ft.Colors.RED_400)

        self.seq_panel.run_button.content=ft.Row(
            [ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED), ft.Text("RUN BOT", weight="bold", size=18)],
            alignment=ft.MainAxisAlignment.CENTER,
        )
        self.seq_panel.run_button.style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.BLUE_600,
            shape=ft.RoundedRectangleBorder(radius=8),
        )

        if self.app.overlay:
            self.app.overlay.stop()

        self.bot = None
        if self.app: self.app.bot = self.bot
        if self.page: self.update()

    def sequence_worker(self):
        try:
            while self.is_running_sequence:
                for item in self.bot_sequence:
                    if not self.is_running_sequence: break
                    if not self.bot: break

                    while self.is_running_sequence and self.bot and self.bot.paused:
                        time.sleep(0.5)
                    
                    task_type = item.get("type")
                    if not task_type or task_type not in COMMAND_TYPES:
                        continue
                    task_info = COMMAND_TYPES[task_type]
                    if self.app.overlay:
                        self.app.overlay.send_update(
                            status="Running", 
                            task=task_info['label'], 
                            paused=False
                        )

                    func_name = COMMAND_TYPES[item["type"]]["func"]
                    self.seq_panel.update_status(f"Executing: {item['type']}", ft.Colors.GREEN_400)
                    
                    # Execute on bot
                    bot_func = getattr(self.bot, func_name, None)
                    if callable(bot_func):
                        self.bot.check_login()
                        if item["type"] == "travel_to":
                            if item["data"]["destination"] == "market":
                                bot_func(item["data"]["market_city"])
                            else:
                                bot_func(item["data"]["island_name"])
                        else:
                            bot_func()
                    elif item["type"] == "wait_time":
                        time_wait = float(item["data"]["minutes"]) * 60
                        for _ in range(int(time_wait)):
                            time.sleep(1)
                            self.bot._wait_if_paused()

                if not self.loop_sequence: break
        except Exception as e:
            print(f"Sequence Error: {e}")
            self.stop_sequence()
        finally:
            self.stop_sequence()

    def change_tab(self, event):
        self.content = ft.ResponsiveRow(
            controls=[self.left_panel, self.right_panels[event.control.data]], spacing=0
        )
        self.update()


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
