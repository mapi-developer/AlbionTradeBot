import flet as ft
import threading
import asyncio
import time
import keyboard
import os
from components import BotOverlay
from bot import Bot, SettingsHandler
import requests
from datetime import datetime
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gui.app import GuiApp

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.components.style import GuiStyle

COMMAND_TYPES = {
    "travel_to": {
        "label": "Travel to",
        "icon": ft.Icons.NAVIGATION_ROUNDED,
        "color": ft.Colors.BLUE_500,
        "func": "travel_to",
    },
    "price_check_fast": {
        "label": "Price Check (Fast Sale)",
        "icon": ft.Icons.SEARCH_ROUNDED,
        "color": ft.Colors.PURPLE_500,
        "func": "check_price_fast",
    },
    "price_check_orders": {
        "label": "Price Check (Orders)",
        "icon": ft.Icons.SEARCH_ROUNDED,
        "color": ft.Colors.PURPLE_800,
        "func": "check_price_orders",
    },
    "buy_items": {
        "label": "Buy items",
        "icon": ft.Icons.SHOPPING_CART_ROUNDED,
        "color": GuiStyle.Colors.ACCENT_GREEN,
        "func": "buy_items",
    },
    "update_orders": {
        "label": "Update Orders",
        "icon": ft.Icons.RECYCLING_OUTLINED,
        "color": "#CBC50C",
        "func": "update_orders",
    },
    "remove_orders": {
        "label": "Remove orders",
        "icon": ft.Icons.CANCEL_ROUNDED,
        "color": GuiStyle.Colors.ACCENT_RED,
        "func": "remove_orders",
    },
    "wait_time": {
        "label": "Wait time",
        "icon": ft.Icons.TIMER_OUTLINED,
        "color": GuiStyle.Colors.ACCENT_ORANGE,
        "func": "wait_time",
    },
    "sell_items": {
        "label": "Sell Items",
        "icon": ft.Icons.SELL_OUTLINED,
        "color": "#872fb7",
        "func": "sell_items"
    }
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
                color=GuiStyle.Colors.TEXT_PRIMARY,
                shape=ft.RoundedRectangleBorder(radius=0),
                bgcolor=ft.Colors.TRANSPARENT,
                shadow_color=ft.Colors.TRANSPARENT,
                text_style=ft.TextStyle(size=18),
                padding=ft.padding.only(0, 15, 0, 15),
                overlay_color=GuiStyle.Colors.CARD_BG,
            ),
        )


class LeftPanel(ft.Column):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.spacing = 0

        self.dashboard_button = LeftPanelButton("Dashboard", "dashboard").content
        self.sequence_button = LeftPanelButton("Bot Sequence", "sequence").content
        self.logs_button = LeftPanelButton("Activity Logs", "logs").content

        upper_buttons = ft.Column(
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

        lower_buttons = ft.Column(
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
                    controls=[upper_buttons, lower_buttons],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                bgcolor=GuiStyle.Colors.SIDEBAR_BG,
            )
        ]


class InfoCard(ft.Container):
    def __init__(self, title: str, icon: str, value: str = "Data Loading..."):
        super().__init__()
        self.col = {"xs": 12, "sm": 6, "md": 3}
        self.display_value = ft.Text(
            value=value,
            size=24,
            weight=ft.FontWeight.BOLD,
            color=GuiStyle.Colors.TEXT_PRIMARY,
        )
        self.content = ft.Container(
            content=ft.Container(
                padding=15,
                content=ft.Column(
                    controls=[
                        ft.ResponsiveRow(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Icon(icon, color=GuiStyle.Colors.GREY_TEXT),
                                        ft.Text(title, size=12, color=GuiStyle.Colors.WHITE_70),
                                    ]
                                ),
                                ft.Column(
                                    controls=[self.display_value],
                                    spacing=5,
                                ),
                            ]
                        ),
                    ]
                ),
            ),
            bgcolor=GuiStyle.Colors.CARD_BG,
            border_radius=15,
            border=ft.border.all(width=1, color=GuiStyle.Colors.BORDER_DEFAULT),
            margin=ft.margin.only(5, 0, 5, 0)
        )

    def set_data(self, new_value: str):
        self.display_value.value = str(new_value)
        self.update()


class OverviewPanel(ft.Container):
    def __init__(self, dashboard):
        super().__init__()
        self.dashboard = dashboard

        self.last_prices_update = InfoCard("Last Prices Update (UTC)", ft.Icons.UPDATE, "Loading...")
        self.database_status = InfoCard("Database Status", ft.Icons.ACCOUNT_TREE, "Loading...")
        self.bot_status = InfoCard("Bot Status", ft.Icons.ADB)
        self.subscribed_until = InfoCard("Subscribed until", ft.Icons.ADD_TASK, "Loading...")

        self.content = ft.ResponsiveRow(
            controls=[
                self.last_prices_update,
                self.database_status,
                self.bot_status,
                self.subscribed_until,
            ],
            spacing=5,
        )

    def did_mount(self):
        self.update_data()

    def update_data(self):
        thread = threading.Thread(target=self._get_data_background, daemon=True)
        thread.start()

    def _get_data_background(self):
        try:
            status_res = requests.get(f"{self.dashboard.API_URL}/")
            status = "Error"
            if status_res.status_code == 200:
                data = status_res.json()
                status = data.get("status")

            last_update_res = requests.get(
                f"{self.dashboard.API_URL}/items/?item_names=T4_SHOES_PLATE_UNDEAD&type=fast"
            )
            formatted_date = "Unknown"
            if last_update_res.status_code == 200:
                data = last_update_res.json()
                if data and len(data) > 0:
                    last_update = data[0].get("updated_at")
                    if last_update:
                        dt_object = datetime.fromisoformat(
                            last_update.replace("Z", "+00:00")
                        )
                        formatted_date = dt_object.strftime("%d.%m.%Y | %H:%M")

            headers = {"Authorization": f"Bearer {self.dashboard.login.state.token}"}
            res = requests.get(
                f"{self.dashboard.API_URL}/users/{self.dashboard.login.state.user_id}",
                headers=headers,
            )
            sub_formatted_date = "Loading"

            if res.status_code == 200:
                data = res.json()
                subscribed_until = data.get("subscribed_until")
                if subscribed_until:
                    dt_object = datetime.fromisoformat(
                        subscribed_until.replace("Z", "+00:00")
                    )
                    sub_formatted_date = dt_object.strftime("%d.%m.%Y")
                else:
                    sub_formatted_date = "Not Active"

            if self.page:
                self.last_prices_update.set_data(formatted_date)
                self.database_status.set_data(
                    "Connected" if status == "alive" else "Not Connected"
                )
                self.bot_status.set_data("Alive")
                self.subscribed_until.set_data(sub_formatted_date)
        except Exception as e:
            print(f"Error updating data: {e}")


class OrdersGraph(ft.Container):
    def __init__(self, max_y: int = 40):
        super().__init__()
        self.padding = 20
        self.bgcolor = GuiStyle.Colors.CARD_BG
        self.border_radius = 15
        self.border = ft.border.all(1, GuiStyle.Colors.BORDER_DEFAULT)
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
                    color=GuiStyle.Colors.WHITE_70,
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
            tooltip_bgcolor=ft.Colors.with_opacity(0.8, GuiStyle.Colors.DARK_BLUE),
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
                ft.Text("Order Activity (Last 3 Days)", size=16, weight=ft.FontWeight.BOLD, color=GuiStyle.Colors.TEXT_PRIMARY),
                ft.Container(height=10),
                ft.Container(content=self.chart, height=300),
            ]
        )


class RightPanel(ft.Column):
    def __init__(self, content_controls=[], scroll_mode=ft.ScrollMode.AUTO, expand_content=False):
        super().__init__()
        self.scroll = scroll_mode
        self.expand = True
        self.col = {"sm": 10.5, "md": 10.5, "xl": 10.5}
        self.controls = [
            ft.Container(
                content=ft.Column(spacing=0, controls=content_controls, expand=expand_content),
                bgcolor=ft.Colors.TRANSPARENT,
                padding=ft.padding.only(20, 10, 20, 0),
                expand=True,
            )
        ]


class DashboardPanel(RightPanel):
    def __init__(self, dashboard):
        self.title = ft.Container(
            content=ft.ResponsiveRow(
                controls=[ft.Text("Bot Overview", size=30, weight=ft.FontWeight.BOLD, color=GuiStyle.Colors.TEXT_PRIMARY)],
            ),
            padding=ft.padding.only(0, 0, 0, 10),
        )
        self.overview_panel = OverviewPanel(dashboard=dashboard)
        self.orders_graph = OrdersGraph()
        super().__init__(
            content_controls=[
                self.title,
                ft.Divider(color=GuiStyle.Colors.BORDER_DEFAULT),
                self.overview_panel,
                ft.Divider(color=GuiStyle.Colors.BORDER_DEFAULT),
                self.orders_graph,
            ]
        )


class BotExecutionWarning(ft.Container):
    def __init__(self):
        super().__init__()
        self.content = ft.Row(
            controls=[
                ft.Icon(ft.Icons.INFO_OUTLINE, color=GuiStyle.Colors.WARNING_TRAVEL_TEXT, size=20, offset=ft.Offset(0, 0.1)),
                ft.Text(
                    "Bot will automatically travel from and to specified island at start and end.", 
                    size=16, color=GuiStyle.Colors.WARNING_TRAVEL_TEXT, expand=True
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
        self.bgcolor = GuiStyle.Colors.LIGHT_BLUE
        self.padding = 15
        self.border_radius = 12
        self.border = ft.border.all(1, GuiStyle.Colors.BORDER_DEFAULT)


class AddSequenceFunctionButton(ft.ElevatedButton):
    def __init__(self, cmd_id: str):
        super().__init__()
        self.data = cmd_id
        self.style = ft.ButtonStyle(
            padding=ft.padding.only(10, 15, 10, 15),
            bgcolor=GuiStyle.Colors.GRAY_BLUE,
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
                ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, color=ft.Colors.WHITE, size=18),
            ]
        )


class FunctionsAvaliablePanel(ft.Container):
    def __init__(self, login):
        super().__init__()
        self.login = login
        self.title = ft.Text(
            value="FUNCTIONS AVAILABLE",
            size=15,
            weight="bold",
            color=GuiStyle.Colors.TEXT_SECONDARY,
            style=ft.TextStyle(letter_spacing=1.2),
            width=float("inf"),
        )
        self.bgcolor = GuiStyle.Colors.CARD_BG
        self.padding = ft.padding.only(20, 15, 20, 20)
        self.border_radius = 15
        self.border = ft.border.all(1, GuiStyle.Colors.BORDER_DEFAULT)

        self.travel_to_button = AddSequenceFunctionButton("travel_to")
        self.price_check_button = AddSequenceFunctionButton("price_check_fast")
        self.price_check_order_button = AddSequenceFunctionButton("price_check_orders")
        self.buy_items_button = AddSequenceFunctionButton("buy_items")
        self.remove_orders_button = AddSequenceFunctionButton("remove_orders")
        self.wait_time_button = AddSequenceFunctionButton("wait_time")
        self.sell_items_button = AddSequenceFunctionButton("sell_items")
        self.update_orders_button = AddSequenceFunctionButton("update_orders")

        self.buttons = {
            "travel_to": self.travel_to_button,
            "price_check_fast": self.price_check_button,
            "price_check_orders": self.price_check_order_button,
            "buy_items": self.buy_items_button,
            "sell_items": self.sell_items_button,
            "remove_orders": self.remove_orders_button,
            "wait_time": self.wait_time_button,
            "update_orders": self.update_orders_button,
        }

        self.content = ft.Column(
            controls=[
                self.title,
                self.travel_to_button,
                self.price_check_button,
                self.buy_items_button,
                self.update_orders_button,
                self.sell_items_button,
                self.remove_orders_button,
                self.wait_time_button,
            ]
        )

        if login.state.user_id == "1":
            self.content.controls.append(self.price_check_order_button)


class TravelToAdditionalInfo(ft.Container):
    def __init__(self, initial_data=None, on_change_callback=None):
        super().__init__()
        self.col = {"sm": 7, "md": 7, "xl": 7}
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
                    ft.DropdownOption(key="island", text="Island"),
                ],
                on_change=self.on_destination_type_change,
                bgcolor=GuiStyle.Colors.DARK_BLUE,
                color=GuiStyle.Colors.TEXT_PRIMARY,
            ),
            col={"sm": 5, "md": 5, "xl": 4},
        )

        self.market_name = ft.Container(
            content=ft.Dropdown(
                expand=True,
                value=market_val,
                label="Market City",
                options=[
                    ft.DropdownOption(key="3003", text="Black Market"),
                    ft.DropdownOption(key="4002", text="Fort Sterling"),
                    ft.DropdownOption(key="1002", text="Lymhurst"),
                    ft.DropdownOption(key="2004", text="Bridgewatch"),
                    ft.DropdownOption(key="3004", text="Martlock"),
                    ft.DropdownOption(key="0007", text="Thetford"),
                    ft.DropdownOption(key="3005", text="Caerleon"),
                    ft.DropdownOption(key="5003", text="Brecilien"),
                ],
                on_change=lambda _: self.trigger_save(),
                bgcolor=GuiStyle.Colors.DARK_BLUE,
                color=GuiStyle.Colors.TEXT_PRIMARY,
            ),
            col={"sm": 7, "md": 7, "xl": 7},
            visible=(dest_val == "market"),
        )

        self.island_name = ft.Container(
            content=ft.TextField(
                expand=True,
                value=island_val,
                label="Island Name",
                on_change=lambda _: self.trigger_save(),
                bgcolor=GuiStyle.Colors.DARK_BLUE,
                color=GuiStyle.Colors.TEXT_PRIMARY,
            ),
            col={"sm": 7, "md": 7, "xl": 7},
            visible=(dest_val == "island"),
        )

        self.content = ft.ResponsiveRow(controls=[self.destination_type, self.market_name, self.island_name])

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
            "island_name": self.island_name.content.value,
        }


class WaitTimeAdditionalInfo(ft.Container):
    def __init__(self, initial_data=None, on_change_callback=None):
        super().__init__()
        self.col = {"sm": 7, "md": 7, "xl": 7}
        self.on_change_callback = on_change_callback
        val = initial_data.get("minutes", "5") if initial_data else "5"

        self.wait_time_amount = ft.Container(
            content=ft.TextField(
                expand=True,
                value=val,
                label="Minutes",
                on_change=lambda _: self.trigger_save(),
                bgcolor=GuiStyle.Colors.DARK_BLUE,
                color=GuiStyle.Colors.TEXT_PRIMARY,
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
    def __init__(
        self,
        function_type: str,
        can_be_removed: bool = False,
        initial_data=None,
        on_change_callback=None,
    ):
        super().__init__()
        self.function_type = function_type
        self.index = ft.Container(
            content=ft.Text("0", color=GuiStyle.Colors.TEXT_PRIMARY), 
            col={"sm": 0.6}, alignment=ft.alignment.center,
        )
        self.title = ft.Text(
            COMMAND_TYPES[function_type]["label"], size=18, weight="bold", 
            col={"sm": 3}, color=GuiStyle.Colors.TEXT_PRIMARY,
        )
        self.icon = ft.Container(
            col={"sm": 0.7},
            aspect_ratio=1,
            bgcolor=COMMAND_TYPES[function_type]["color"],
            border_radius=4,
            alignment=ft.alignment.center,
            content=ft.Icon(name=COMMAND_TYPES[function_type]["icon"], color="#ffffff"),
        )

        self.remove_btn_container = ft.Container(
            content=ft.IconButton(icon=ft.Icons.DELETE, icon_color=GuiStyle.Colors.ACCENT_RED),
            col={"sm": 1},
            alignment=ft.alignment.center_right,
        )
        self.remove_button = self.remove_btn_container.content

        self.additional_info = ft.Container(col={"sm": 7, "md": 7, "xl": 7})
        if function_type == "travel_to":
            self.additional_info = TravelToAdditionalInfo(initial_data, on_change_callback)
        elif function_type == "wait_time":
            self.additional_info = WaitTimeAdditionalInfo(initial_data, on_change_callback)

        self.padding = 10
        self.bgcolor =  GuiStyle.Colors.INNER_BG
        self.border_radius = 8
        self.content = ft.ResponsiveRow(
            controls=[
                ft.ResponsiveRow(
                    controls=[self.index, self.icon, self.title, self.additional_info],
                    spacing=20,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    col={"sm": 10},
                ),
                self.remove_btn_container if can_be_removed else ft.Container(col=1),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
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

        self.content = ft.Column(
            controls=[],
            scroll=ft.ScrollMode.AUTO,
        )
        self.update_indexes()

    def load_sequence(self, sequence_data):
        self.content.controls.clear()
        for i, item in enumerate(sequence_data):
            func_type = item.get("type", "price_check")

            can_be_removed = True
            if (
                i == 0
                and len(
                    [
                        function["type"]
                        for function in sequence_data
                        if function["type"] == "travel_to"
                    ]
                )
                > 1
            ):
                can_be_removed = False

            new_func = FunctionToExecute(
                func_type,
                can_be_removed=can_be_removed,
                initial_data=item.get("data"),
                on_change_callback=self.dashboard.save_sequence,
            )

            self.content.controls.append(new_func)

        self.update_indexes()

    def add_function(self, event):
        new_function = FunctionToExecute(
            event.control.data,
            can_be_removed=True,
            on_change_callback=self.dashboard.save_sequence,
        )
        travel_to_amount = len(
            [
                function.function_type
                for function in self.content.controls
                if function.function_type == "travel_to"
            ]
        )
        if (
            travel_to_amount == 0
            and new_function.function_type == "travel_to"
            and len(self.content.controls) != 0
        ):
            init_travel = FunctionToExecute(
                event.control.data,
                can_be_removed=False,
                on_change_callback=self.dashboard.save_sequence,
            )
            self.content.controls.insert(0, init_travel)
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

            if function.function_type == "travel_to":
                travel_amount = len(
                    [
                        function.function_type
                        for function in self.content.controls
                        if function.function_type == "travel_to"
                    ]
                )
                if i == 0 and travel_amount > 1:
                    function.content.controls[1] = ft.Container(col=1)
                elif i == 0:
                    function.content.controls[1] = function.remove_btn_container

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
            on_change=self.loop_toggle,
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
            offset=ft.Offset(0, 0.1),
            color=GuiStyle.Colors.TEXT_PRIMARY,
        )
        def on_home_island_changed(event):
            self.dashboard.config.set("home_island", event.data)
        self.home_island = ft.TextField(
            label="End Island Name",
            value=self.dashboard.config.get("home_island"),
            text_size=12,
            col=4,
            prefix_icon=ft.Icons.MAP_OUTLINED,
            bgcolor=GuiStyle.Colors.DARK_BLUE,
            color=GuiStyle.Colors.TEXT_PRIMARY,
            on_change=on_home_island_changed
        )

        self.wait_before_loop = ft.TextField(
            label="Wait before repeat (minutes)",
            col={"sm": 6, "md": 5, "xl": 6},
            visible=False,
        )

        self.bot_status = ft.Container(
            content=ft.Row(
                [
                    self.status_indicator,
                    ft.Text(
                        "Bot State:",
                        size=12,
                        color=GuiStyle.Colors.GREY_TEXT,
                        weight="bold",
                    ),
                    self.status_text,
                ],
                spacing=10,
            ),
            bgcolor=GuiStyle.Colors.BOT_STATUS_BG,
            padding=ft.padding.symmetric(15, 10),
            border_radius=10,
            border=ft.border.all(1, "#1e293b"),
            col={"sm": 4, "md": 4, "xl": 4},
        )

        self.lower_row = ft.ResponsiveRow(
            controls=[
                ft.ResponsiveRow(
                    controls=[
                        self.loop_checkbox,
                        self.wait_before_loop,
                    ],
                    col={"sm": 8, "md": 8, "xl": 8},
                ),
                ft.Column(
                    controls=[
                        self.bot_status,
                    ],
                    col={"sm": 4, "md": 4, "xl": 4},
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

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
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            height=45,
            col={"sm": 5, "md": 3.5, "xl": 2.45},
            on_click=self.bot_toggle,
            data="run",
        )

        self.bgcolor = GuiStyle.Colors.CARD_BG
        self.padding = ft.padding.only(20, 15, 20, 20)
        self.border_radius = 15
        self.border = ft.border.all(1, GuiStyle.Colors.BORDER_DEFAULT)
        self.content = ft.Column(
            controls=[
                ft.ResponsiveRow(
                    controls=[
                        title,
                        self.home_island,
                    ],
                    vertical_alignment=ft.VerticalAlignment.CENTER,
                ),
                ft.Divider(color=GuiStyle.Colors.BORDER_DEFAULT),
                self.execution_functions_list,
                ft.Divider(color=GuiStyle.Colors.BORDER_DEFAULT),
                ft.Container(
                    content=self.lower_row, padding=ft.padding.only(0, 0, 0, 10)
                ),
                ft.ResponsiveRow(
                    controls=[self.run_button], alignment=ft.MainAxisAlignment.END
                ),
            ],
            width=float("inf"),
        )

    def bot_toggle(self, e):
        self.run_button.disabled = True
        self.run_button.content = ft.Row(
            [
                ft.Icon(ft.Icons.PAUSE_ROUNDED),
                ft.Text("STARTING", weight="bold", size=18),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )
        self.run_button.style = ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=GuiStyle.Colors.RUN_BUTTON_TOGGLE,
            shape=ft.RoundedRectangleBorder(radius=8),
        )
        if self.page:
            self.run_button.update()

        if self.run_button.data == "run":
            self.run_button.content = ft.Row(
                [
                    ft.Icon(ft.Icons.PAUSE_ROUNDED),
                    ft.Text("STOP", weight="bold", size=18),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            )
            self.run_button.style = ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=GuiStyle.Colors.ACCENT_RED,
                shape=ft.RoundedRectangleBorder(radius=8),
            )
            self.dashboard.start_sequence()
            self.run_button.data = "stop"
            self.run_button.disabled = False
        elif self.run_button.data == "stop":
            self.dashboard.bot.stop()
            self.run_button.content = ft.Row(
                [
                    ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED),
                    ft.Text("RUN BOT", weight="bold", size=18),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            )
            self.run_button.style = ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=GuiStyle.Colors.ACCENT_BLUE,
                shape=ft.RoundedRectangleBorder(radius=8),
            )
            if self.dashboard.bot.status == "Running":
                self.dashboard.bot.toggle_pause()
                time.sleep(1)
            self.dashboard.stop_sequence()
            self.run_button.data = "run"
            self.run_button.disabled = False

        if self.page:
            self.run_button.update()

    def loop_toggle(self, e):
        if self.loop_checkbox.value:
            self.wait_before_loop.visible = False
            self.dashboard.loop_sequence = True
        else:
            self.wait_before_loop.visible = False
            self.dashboard.loop_sequence = False

        self.update()

    def update_status(self, text: str, color: str):
        self.status_text.value = text
        self.status_indicator.bgcolor = color
        if self.page:
            self.update()


class BotControlPanel(ft.Container):
    def __init__(self, dashboard, login):
        super().__init__()
        left_side_size = 3
        self.padding = ft.padding.only(0, 10, 0, 0)

        self.execution_warning = BotExecutionWarning()
        self.execution_sequence_panel = ExecutionSequencePanel(dashboard)
        self.functions_avaliable_panel = FunctionsAvaliablePanel(login)

        for key in self.functions_avaliable_panel.buttons:
            execution_list = self.execution_sequence_panel.execution_functions_list
            self.functions_avaliable_panel.buttons[key].on_click = (
                execution_list.add_function
            )

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


class SubscriptionBlocker(ft.Container):
    def __init__(self, on_shop_click):
        super().__init__()
        self.bgcolor = ft.Colors.with_opacity(0.8, "#131415")
        self.alignment = ft.alignment.center
        self.expand = True
        self.border_radius = 10
        self.content = ft.Column(
            controls=[
                ft.Icon(ft.Icons.LOCK_OUTLINE, size=64, color=GuiStyle.Colors.ACCENT_RED),
                ft.Text("Subscription Required", size=24, weight=ft.FontWeight.BOLD, color=GuiStyle.Colors.TEXT_PRIMARY),
                ft.Text(
                    "This feature is only available for active subscribers.",
                    size=16,
                    color=GuiStyle.Colors.TEXT_SECONDARY,
                ),
                ft.Container(height=20),
                ft.ElevatedButton(
                    text="Go to Shop",
                    icon=ft.Icons.SHOPPING_BAG,
                    style=ft.ButtonStyle(
                        bgcolor=GuiStyle.Colors.ACCENT_ORANGE, color=GuiStyle.Colors.WHITE, padding=20
                    ),
                    on_click=on_shop_click,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        )


class BotSequencePanel(RightPanel):
    def __init__(self, dashboard, login):
        self.dashboard = dashboard
        self.title = ft.Container(
            content=ft.ResponsiveRow(
                controls=[
                    ft.Text(
                        value="Configure Bot Sequence",
                        size=30,
                        weight=ft.FontWeight.BOLD,
                        col={"sm": 12, "md": 12, "xl": 12},
                        color=GuiStyle.Colors.TEXT_PRIMARY
                    )
                ],
            ),
            padding=ft.padding.only(0, 0, 0, 10),
        )

        self.bot_control_panel = BotControlPanel(dashboard=dashboard, login=login)

        # 1. Main UI content inside the layout container with padding
        self.content_layout = ft.Container(
            content=ft.Column(
                controls=[
                    self.title,
                    ft.Divider(color=GuiStyle.Colors.BORDER_DEFAULT),
                    self.bot_control_panel,
                ],
                spacing=0,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=ft.padding.only(20, 10, 20, 0),
            expand=True,
        )

        # 2. Blocker covers everything (Overlay)
        self.blocker = SubscriptionBlocker(
            on_shop_click=lambda e: self.dashboard.app.go_to_subscription()
        )
        self.blocker.visible = False

        # 3. Stack wraps both, allowing blocker to sit on top of the padded container
        self.main_stack = ft.Stack(
            controls=[self.content_layout, self.blocker], expand=True
        )

        # 4. Initialize RightPanel
        # We override the controls list directly to bypass the default padding container
        super().__init__()
        self.controls = [
            ft.Container(
                content=self.main_stack,
                bgcolor=ft.Colors.TRANSPARENT,
                padding=0,  # No padding on the outer container
                expand=True,
            )
        ]
        self.expand = True
        self.scroll = None

    def show_tab(self):
        if self.dashboard.header and self.dashboard.header.subscription:
            is_subscribed = self.dashboard.header.subscription.is_active
            self.blocker.visible = not is_subscribed
            self.bot_control_panel.disabled = not is_subscribed
            avaliable_functions = self.bot_control_panel.functions_avaliable_panel
            if avaliable_functions.login.state.user_id == "1" and not avaliable_functions.price_check_order_button in avaliable_functions.content.controls:
                avaliable_functions.content.controls.append(avaliable_functions.price_check_order_button)
            elif avaliable_functions.price_check_order_button in avaliable_functions.content.controls and avaliable_functions.login.state.user_id != "1":
                avaliable_functions.content.controls.remove(avaliable_functions.price_check_order_button)
            if self.page:
                self.update()


class ActivityLogItem(ft.Container):
    def __init__(self, dashboard, title: str, on_click=None, on_delete=None, data=None):
        super().__init__()
        
        current = dashboard.app.logger.current_session_file
        self.open_button = ft.ElevatedButton(
            content=ft.Row(
                controls=[
                    ft.Text(
                        value=title,
                        weight="bold",
                        size=20,  # Slightly smaller to fit nicely
                        color="#ffffff",
                        expand=True,
                    )
                ]
            ),
            style=ft.ButtonStyle(
                padding=ft.padding.all(20),
                bgcolor=GuiStyle.Colors.CARD_BG,
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(1, GuiStyle.Colors.BORDER_DEFAULT),
            ),
            on_click=on_click,
            data=data,
            expand=True,  # This makes the button take all available space
        )

        # 2. Delete Button
        self.delete_button = ft.Container(
            content=ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE,
                icon_color=GuiStyle.Colors.ACCENT_RED,
                icon_size=24,
                tooltip="Delete Log",
                on_click=on_delete,
                data=data,
            ),
            bgcolor=GuiStyle.Colors.CARD_BG,  # Darker background for the delete action
            border_radius=8,
            alignment=ft.alignment.center,
            padding=5,
            border=ft.border.all(1, GuiStyle.Colors.BORDER_DEFAULT)
        )

        # 3. Layout
        self.content = ft.Row(
            controls=[self.open_button],
            spacing=10,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        if current and not os.path.basename(current) == data:
            self.content.controls.append(self.delete_button)
            self.open_button.content.controls[0].color = GuiStyle.Colors.TEXT_SECONDARY            


class LogsView(ft.Container):
    class LogRow(ft.Row):
        def __init__(self, category: str, message: str, color: str):
            super().__init__()
            self.vertical_alignment = ft.CrossAxisAlignment.START
            self.controls = [
                ft.Container(
                    content=ft.Text(
                        category.upper(), size=10, weight="bold", color=ft.Colors.BLACK
                    ),
                    bgcolor=color,
                    padding=ft.padding.symmetric(horizontal=5, vertical=2),
                    border_radius=3,
                    width=70,
                    alignment=ft.alignment.center,
                ),
                ft.Text(message, size=13, font_family="monospace", expand=True),
            ]

    def __init__(self, initial_logs=None):
        super().__init__()
        self.padding = 10
        self.border = ft.border.all(1, ft.Colors.OUTLINE_VARIANT)
        self.border_radius = 8
        self.bgcolor = ft.Colors.BLACK12
        self.expand = True

        self.log_column = ft.Column(
            scroll=ft.ScrollMode.AUTO, spacing=5, auto_scroll=True
        )

        self.content = self.log_column

        if initial_logs:
            self.add_logs(initial_logs)

    def clear_logs(self):
        self.log_column.controls.clear()
        if self.page:
            self.update()

    def set_logs(self, log_list: list[str]):
        self.log_column.controls.clear()
        self.add_logs(log_list)

    def add_logs(self, log_list: list[str]):
        for entry in log_list:
            if ";" in entry:
                category, message = entry.split(";", 1)
                color = GuiStyle.Colors.LOG_COLORS.get(category.lower(), ft.Colors.GREY_400)
                self.log_column.controls.append(self.LogRow(category, message, color))
        if self.page:
            self.update()


class ActivityLogsPanel(RightPanel):
    def __init__(self, dashboard=None):
        super().__init__()
        self.expand = True
        self.dashboard = dashboard  # Store reference to dashboard (and app)

        self.back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
            icon_size=20,
            on_click=lambda _: self.show_logs_list(),
            visible=False,
            icon_color=GuiStyle.Colors.WHITE,
        )
        self.title_text = ft.Text(
            value="Bot Activity Logs",
            size=30,
            weight=ft.FontWeight.BOLD,
            color=GuiStyle.Colors.TEXT_PRIMARY,
        )
        self.title_container = ft.Container(
            content=ft.Row(
                controls=[self.back_button, self.title_text],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.only(0, 0, 0, 10),
        )

        self.logs_list_content = ft.Column(
            controls=[], spacing=10  # Populated dynamically
        )

        self.logs_view = LogsView()
        self.logs_view.visible = False
        self.logs_view.margin = ft.margin.only(0, 10, 0, 20)

        self.inner_column = self.controls[0].content

        # Initialize with logs
        self.refresh_logs()
        self._setup_initial_view()

    def format_log_title(self, filename):
        # filename: 23.12.2025-14.42.json
        # output: 23.12.2025 | 14:42 UTC
        try:
            name = os.path.splitext(filename)[0]
            date_part, time_part = name.split("-")
            time_formatted = time_part.replace(".", ":")
            return f"{date_part} | {time_formatted} UTC"
        except:
            return filename

    def refresh_logs(self):
        files = []
        if self.dashboard and self.dashboard.config:
            files = self.dashboard.config.get_logs()

        self.logs_list_content.controls.clear()

        for f in files:
            title = self.format_log_title(f)

            if (
                self.dashboard
                and self.dashboard.app
                and hasattr(self.dashboard.app, "logger")
            ):
                current = self.dashboard.app.logger.current_session_file
                if current and os.path.basename(current) == f:
                    title += " | Current Session"

            self.logs_list_content.controls.append(
                ActivityLogItem(
                    self.dashboard, title, on_click=self.handle_log_click, data=f
                )
            )
        if self.page:
            self.update()

    def _setup_initial_view(self):
        self.scroll = ft.ScrollMode.AUTO
        self.back_button.visible = False
        self.title_text.value = "Bot Activity Logs"
        self.logs_list_content.visible = True
        self.logs_view.visible = False
        self.logs_view.expand = False

        self.inner_column.controls = [
            self.title_container,
            ft.Divider(color=GuiStyle.Colors.BORDER_DEFAULT),
            self.logs_list_content,
        ]

    def handle_log_click(self, e):
        filename = e.control.data
        if filename and self.dashboard and self.dashboard.config:
            data = self.dashboard.config.get_log(filename)
            self.logs_view.set_logs(data)
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
            ft.Divider(color=GuiStyle.Colors.BORDER_DEFAULT),
            self.logs_list_content,
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
            ft.Divider(color=GuiStyle.Colors.BORDER_DEFAULT),
            self.logs_view,
        ]

        if self.page:
            self.update()

    def refresh_logs(self):
        files = []
        if self.dashboard and self.dashboard.config:
            files = self.dashboard.config.get_logs()

        self.logs_list_content.controls.clear()

        for f in files:
            title = self.format_log_title(f)

            if (
                self.dashboard
                and self.dashboard.app
                and hasattr(self.dashboard.app, "logger")
            ):
                current = self.dashboard.app.logger.current_session_file
                if current and os.path.basename(current) == f:
                    title += " | Current Session"

            self.logs_list_content.controls.append(
                ActivityLogItem(
                    self.dashboard,
                    title,
                    on_click=self.handle_log_click,
                    on_delete=self.handle_log_delete,
                    data=f,
                )
            )
        if self.page:
            self.update()

    def handle_log_delete(self, e):
        """Deletes the log file and refreshes the list."""
        filename = e.control.data
        if not filename:
            return

        if self.dashboard and self.dashboard.config:
            success = self.dashboard.config.delete_log(filename)
            if success:
                print(f"Deleted log: {filename}")
                self.refresh_logs()

                if self.logs_view.visible:
                    self.show_logs_list()


class Dashboard(ft.Container):
    bot: Bot | None

    def __init__(
        self,
        app: "GuiApp",
        config: SettingsHandler,
        page=None,
        bot: Bot = None,
        header=None,
        login=None,
    ):
        super().__init__()
        self.expand = True
        self.app = app
        self.config = config
        self.page = page
        self.bot = bot
        self.login = login
        self.header = header
        self.API_URL = self.config.API_URL

        self.is_running_sequence = False
        self.loop_sequence = False
        self.bot_sequence = self.config.load_bot_loop() if self.config else []

        self.dashboard_panel = DashboardPanel(dashboard=self)
        self.bot_sequence_panel = BotSequencePanel(dashboard=self, login=self.login)
        self.bot_activity_panel = ActivityLogsPanel(dashboard=self)  # Pass self
        self.left_panel = LeftPanel()

        self.seq_panel = (
            self.bot_sequence_panel.bot_control_panel.execution_sequence_panel
        )
        self.avail_panel = (
            self.bot_sequence_panel.bot_control_panel.functions_avaliable_panel
        )

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
            controls=[self.left_panel, self.dashboard_panel],
            spacing=0,
        )

        try:
            keyboard.remove_hotkey("f1")
        except:
            pass

        try:
            keyboard.add_hotkey("f1", lambda: self._on_global_hotkey())
        except Exception as e:
            print(f"Failed to register global hotkey: {e}")

    def set_ui_lock(self, locked: bool):
        self.seq_panel.home_island.disabled = locked
        self.seq_panel.loop_checkbox.disabled = locked
        self.seq_panel.wait_before_loop.disabled = locked
        self.avail_panel.disabled = locked
        self.seq_panel.execution_functions_list.disabled = locked

        if self.page:
            self.update()

    def save_sequence(self):
        self.bot_sequence = [
            c.get_serialized_data()
            for c in self.seq_panel.execution_functions_list.content.controls
        ]
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
                        paused=paused,
                    )

                status = "PAUSED (F1 to Resume)" if paused else "Running"
                color = ft.Colors.ORANGE_400 if paused else ft.Colors.GREEN_400
                self.seq_panel.update_status(status, color)
            except Exception as e:
                print(f"Hotkey Error: {e}")

    def start_sequence(self):
        if not self.bot_sequence:
            return
        self.app.overlay.start()
        time.sleep(3)
        self.is_running_sequence = True
        self.set_ui_lock(True)
        self.seq_panel.update_status("Initializing...", ft.Colors.BLUE_400)

        threading.Thread(target=self._run_worker_sync, daemon=True).start()

    def stop_sequence(self):
        self.is_running_sequence = False
        self.set_ui_lock(False)
        self.seq_panel.update_status("Stopped", ft.Colors.RED_400)

        self.seq_panel.run_button.content = ft.Row(
            [
                ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED),
                ft.Text("RUN BOT", weight="bold", size=18),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )
        self.seq_panel.run_button.style = ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.BLUE_600,
            shape=ft.RoundedRectangleBorder(radius=8),
        )

        if self.app.overlay:
            self.app.overlay.stop()
        if self.bot != None:
            self.bot.stop()
        self.seq_panel.run_button.data = "run"
        if self.page:
            self.update()

    def _run_worker_sync(self):
        try:
            asyncio.run(self.sequence_worker())
        except Exception as e:
            print(f"Worker Thread Error: {e}")
            self.stop_sequence()

    async def sequence_worker(self):
        try:
            while self.is_running_sequence:
                for item in self.bot_sequence:
                    if not self.is_running_sequence:
                        break
                    if not self.bot:
                        break

                    while self.is_running_sequence and self.bot:
                        time.sleep(0.5)

                    task_type = item.get("type")
                    if not task_type or task_type not in COMMAND_TYPES:
                        continue
                    task_info = COMMAND_TYPES[task_type]
                    if self.app.overlay:
                        self.app.overlay.send_update(
                            status="Running", task=task_info["label"], paused=False
                        )

                    func_name = COMMAND_TYPES[item["type"]]["func"]
                    self.seq_panel.update_status(
                        f"Executing: {item['type']}", ft.Colors.GREEN_400
                    )
                    self.bot.overlay = self.app.overlay
                    bot_func = getattr(self.bot, func_name, None)
                    if callable(bot_func):
                        if item["type"] == "travel_to":
                            if item["data"]["destination"] == "market":
                                await bot_func(item["data"]["market_city"])
                            else:
                                await bot_func(item["data"]["island_name"])
                        else:
                            await bot_func()
                    elif item["type"] == "wait_time":
                        time_wait = float(item["data"]["minutes"]) * 60
                        for _ in range(int(time_wait)):
                            time.sleep(1)
                            await self.bot._can_run.wait()

                functions_list = (
                    self.bot_sequence_panel.bot_control_panel.execution_sequence_panel.execution_functions_list.content.controls
                )
                travel_amount = len(
                    [
                        function.function_type
                        for function in functions_list
                        if function.function_type == "travel_to"
                    ]
                )
                if self.bot.local_player.location.location_id.rsplit('-', 1)[0] != "ISLAND-GUILD" and travel_amount != 0 or self.bot.local_player.location.location_id == "ISLAND-GUILD":
                    bot_func = getattr(self.bot, "travel_to", None)
                    bot_func(self.bot_sequence_panel.bot_control_panel.execution_sequence_panel.home_island.value)

                if self.loop_sequence == False:
                    break
        except Exception as e:
            print(f"Sequence Error: {e}")
            self.stop_sequence()
        finally:
            self.stop_sequence()

    def change_tab(self, event):
        target_tab = event.control.data
        self.content = ft.ResponsiveRow(
            controls=[self.left_panel, self.right_panels[target_tab]], spacing=0
        )

        if target_tab == "sequence":
            self.bot_sequence_panel.show_tab()
        elif target_tab == "logs":
            self.bot_activity_panel.refresh_logs()  # Refresh list when opening logs
        elif target_tab == "dashboard":
            self.dashboard_panel.overview_panel.update_data()

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
