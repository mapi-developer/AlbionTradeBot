import flet as ft
import flet_charts as fch
import threading
import asyncio
import time
import keyboard
import os
from bot import Bot, SettingsHandler
import requests
from datetime import datetime
import sys
import math, json, re
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
            content=ft.Text(text),
            data=data,
            style=ft.ButtonStyle(
                color=GuiStyle.Colors.TEXT_PRIMARY,
                shape=ft.RoundedRectangleBorder(radius=0),
                bgcolor=ft.Colors.TRANSPARENT,
                shadow_color=ft.Colors.TRANSPARENT,
                text_style=ft.TextStyle(size=18),
                padding=ft.Padding.only(left=0, top=15, right=0, bottom=15),
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
                alignment=ft.Alignment.TOP_LEFT,
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
        self.on_hover = self._handle_hover
        
        self.display_value = ft.Text(
            value=value,
            size=24,
            weight=ft.FontWeight.BOLD,
            color=GuiStyle.Colors.TEXT_PRIMARY,
        )
        
        self.main_content = ft.Container(
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
            bgcolor=GuiStyle.Colors.CARD_BG,
            border_radius=15,
            border=ft.Border.all(width=1, color=GuiStyle.Colors.BORDER_DEFAULT),
            expand=True,
        )

        self.popup_content_col = ft.Column(spacing=2)
        
        self.popup_container = ft.Container(
            content=ft.Container(
                content=self.popup_content_col,
                padding=10,
                alignment=ft.Alignment.CENTER
            ),
            bgcolor=GuiStyle.Colors.SIDEBAR_BG, # Slightly darker/different bg for contrast
            border_radius=15,
            border=ft.Border.all(width=1, color=GuiStyle.Colors.ACCENT_BLUE), # Highlight border
            opacity=0, # Invisible by default
            animate_opacity=200, # Smooth fade in
            visible=False, # Hidden from hit-testing when not active
            expand=True, # Overlay the whole card
        )

        self.content = ft.Stack(
            controls=[
                self.main_content,
                self.popup_container
            ]
        )
        
        self.margin = ft.Margin.only(left=5, top=0, right=5, bottom=0)

    def _handle_hover(self, e):
        if e.data == "true" and self.popup_content_col.controls != []:
            self.popup_container.visible = True
            self.popup_container.opacity = 1
        else:
            self.popup_container.opacity = 0
            self.popup_container.visible = False
        self.update()

    def set_data(self, new_value: str, popup_controls: list[ft.Control] = None):
        """
        Updates the main value and optionally the popup content.
        :param new_value: The text to display on the main card.
        :param popup_controls: A list of Controls (e.g. Text rows) to show in the popup.
        """
        self.display_value.value = str(new_value)
        
        if popup_controls:
            self.popup_content_col.controls = popup_controls
        
        self.update()


class OverviewPanel(ft.Container):
    def __init__(self, dashboard: "Dashboard"):
        super().__init__()
        self.dashboard = dashboard

        self.last_prices_update = InfoCard("Prices Up-to-Date", ft.Icons.UPDATE, "Loading...")
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

    def _get_data_background(self, *args, **kwargs):
        try:
            status_res = requests.get(f"{self.dashboard.API_URL}/")
            status = "Error"
            if status_res.status_code == 200:
                data = status_res.json()
                status = data.get("status")

            server = self.dashboard.config.get("general").get("server", "US")
            
            up_to_date_res = requests.get(
                f"{self.dashboard.API_URL}/items/prices-up-to-date",
                params={"server": server}    
            )
            bm_val = "Unknown"
            popup_items = []

            if up_to_date_res.status_code == 200:
                data = up_to_date_res.json()
                
                bm_val = data.get("black_market", "N/A")

                for city in sorted(data.keys()):
                    if city != "black_market":
                        percent = data[city]
                        city_name = city.replace("_", " ").title()
                        
                        row = ft.Row(
                            controls=[
                                ft.Text(f"{city_name}:", size=12, color=GuiStyle.Colors.GREY_TEXT),
                                ft.Text(f"{percent}", size=12, weight=ft.FontWeight.BOLD, color=GuiStyle.Colors.TEXT_PRIMARY),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        )
                        popup_items.append(row)
                
                if not popup_items:
                    popup_items = [ft.Text("No other city data", size=12, color=GuiStyle.Colors.GREY_TEXT)]

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
                self.last_prices_update.set_data(f"Black Market: {bm_val}", popup_controls=popup_items)
                self.database_status.set_data(
                    "Connected" if status == "alive" else "Not Connected"
                )
                self.bot_status.set_data(self.dashboard.bot.get_status())
                self.subscribed_until.set_data(sub_formatted_date)

        except Exception as e:
            print(f"Error updating data: {e}")


class OrdersGraph(ft.Container):
    def __init__(self, dashboard: "Dashboard", max_y: int = 40):
        self.dashboard = dashboard

        # Use ft.LineChartDataPoint
        self.chart_data = [
            fch.LineChartDataPoint(0, 5),
            fch.LineChartDataPoint(1, 12),
            fch.LineChartDataPoint(2, 8),
            fch.LineChartDataPoint(3, 25),
            fch.LineChartDataPoint(4, 15),
            fch.LineChartDataPoint(5, 30),
            fch.LineChartDataPoint(6, 22),
            fch.LineChartDataPoint(7, 5),
            fch.LineChartDataPoint(8, 12),
            fch.LineChartDataPoint(9, 8),
            fch.LineChartDataPoint(10, 25),
        ]

        self.chart = fch.LineChart(
            data_series=[
                fch.LineChartData(
                    points=self.chart_data,
                    stroke_width=4,
                    color=GuiStyle.Colors.WHITE_70,
                    curved=False,
                    point=True,
                )
            ],
            bottom_axis=fch.ChartAxis(
                labels=[
                    fch.ChartAxisLabel(value=2, label=ft.Text("2d ago", size=15)),
                    fch.ChartAxisLabel(value=4, label=ft.Text("1d 12h ago", size=15)),
                    fch.ChartAxisLabel(value=6, label=ft.Text("24h ago", size=15)),
                    fch.ChartAxisLabel(value=8, label=ft.Text("12h ago", size=15)),
                    fch.ChartAxisLabel(value=10, label=ft.Text("Now", size=15)),
                ],
                label_size=30,
            ),
            left_axis=fch.ChartAxis(
                labels=[
                    fch.ChartAxisLabel(value=0, label=ft.Text("0", size=15)),
                    fch.ChartAxisLabel(
                        value=int(max_y / 2),
                        label=ft.Text(str(int(max_y / 2)), size=15),
                    ),
                    fch.ChartAxisLabel(value=max_y, label=ft.Text(str(max_y), size=15)),
                ],
                label_size=30,
            ),
            border=ft.border.Border.all(3, ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE)),
            # Replaced 'tooltip_bgcolor' with 'tooltip=fch.LineChartTooltip(...)'
            tooltip=fch.LineChartTooltip(
                bgcolor=ft.Colors.with_opacity(0.8, GuiStyle.Colors.DARK_BLUE)
            ),
            horizontal_grid_lines=fch.ChartGridLines(
                interval=max_y / 4,
                color=ft.Colors.with_opacity(0.2, ft.Colors.ON_SURFACE),
                width=1,
            ),
            vertical_grid_lines=fch.ChartGridLines(
                interval=1,
                color=ft.Colors.with_opacity(0.2, ft.Colors.ON_SURFACE),
                width=1,
            ),
            min_y=0,
            max_y=max_y,
            expand=True,
        )

        super().__init__(
            padding=20,
            bgcolor=GuiStyle.Colors.CARD_BG,
            border_radius=15,
            border=ft.border.Border.all(1, GuiStyle.Colors.BORDER_DEFAULT),
            margin=ft.margin.Margin.only(top=10),
            content=ft.Column(
                [
                    ft.Text(
                        "Order Activity (Last 3 Days)",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=GuiStyle.Colors.TEXT_PRIMARY,
                    ),
                    ft.Container(height=10),
                    ft.Container(content=self.chart, height=300),
                ]
            ),
        )

    def update_graph_data(self):
        stats = self.dashboard.bot.get_order_stats()
        new_points = []
        max_y = 0
        for i, count in enumerate(stats):
            new_points.append(fch.LineChartDataPoint(i, count))
            if count > max_y:
                max_y = int(count)

        max_y = max(20, int(max_y * 1.2))

        # Updated property name 'points'
        self.chart.data_series[0].points = new_points
        self.chart.left_axis = fch.ChartAxis(
            labels=[
                fch.ChartAxisLabel(value=0, label=ft.Text("0", size=15)),
                fch.ChartAxisLabel(
                    value=int(max_y / 2),
                    label=ft.Text(str(int(max_y / 2)), size=15),
                ),
                fch.ChartAxisLabel(value=max_y, label=ft.Text(str(max_y), size=15)),
            ],
            label_size=30,
        )
        self.chart.horizontal_grid_lines = fch.ChartGridLines(
            interval=max_y / 4,
            color=ft.Colors.with_opacity(0.2, ft.Colors.ON_SURFACE),
            width=1,
        )
        self.chart.vertical_grid_lines = fch.ChartGridLines(
            interval=1,
            color=ft.Colors.with_opacity(0.2, ft.Colors.ON_SURFACE),
            width=1,
        )
        self.chart.min_y = 0
        self.chart.max_y = max_y

        try:
            self.update()
        except RuntimeError:
            pass


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
                padding=ft.Padding.only(left=20, top=10, right=20, bottom=0),
                expand=True,
            )
        ]


class DashboardPanel(RightPanel):
    def __init__(self, dashboard):
        self.title = ft.Container(
            content=ft.ResponsiveRow(
                controls=[ft.Text("Bot Overview", size=30, weight=ft.FontWeight.BOLD, color=GuiStyle.Colors.TEXT_PRIMARY)],
            ),
            padding=ft.Padding.only(left=0, top=0, right=0, bottom=10),
        )
        
        self.overview_panel = OverviewPanel(dashboard=dashboard)
        self.orders_graph = OrdersGraph(dashboard)
        self.market_table = ft.Container(
            content=MarketTable(dashboard),
            padding=ft.Padding.only(left=0, top=0, right=0, bottom=150),
            height=1200
        )

        super().__init__(
            content_controls=[
                self.title,
                ft.Divider(color=GuiStyle.Colors.BORDER_DEFAULT),
                self.overview_panel,
                ft.Divider(color=GuiStyle.Colors.BORDER_DEFAULT),
                self.orders_graph,
                ft.Divider(color=GuiStyle.Colors.BORDER_DEFAULT),
                self.market_table,
            ]
        )


class BotExecutionWarning(ft.Container):
    def __init__(self):
        super().__init__()
        self.content = ft.Row(
            controls=[
                ft.Icon(ft.Icons.INFO_OUTLINE, color=GuiStyle.Colors.WARNING_TRAVEL_TEXT, size=20, offset=ft.Offset(0, 0.1)),
                ft.Text(
                    'You need to change location before to use "Travel to" function', 
                    size=16, color=GuiStyle.Colors.WARNING_TRAVEL_TEXT, expand=True
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
        self.bgcolor = GuiStyle.Colors.LIGHT_BLUE
        self.padding = ft.Padding.only(left=15, top=15, right=15, bottom=15)
        self.border_radius = 12
        self.border = ft.Border.all(1, GuiStyle.Colors.BORDER_DEFAULT)


class AddSequenceFunctionButton(ft.ElevatedButton):
    def __init__(self, cmd_id: str):
        super().__init__()
        self.data = cmd_id
        self.style = ft.ButtonStyle(
            padding=ft.Padding.only(left=10, top=15, right=10, bottom=15),
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
        self.padding = ft.Padding.only(left=20, top=15, right=20, bottom=20)
        self.border_radius = 15
        self.border = ft.Border.all(1, GuiStyle.Colors.BORDER_DEFAULT)

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
                on_select=self.on_destination_type_change,
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
                    ft.DropdownOption(key="3008", text="Martlock"),
                    ft.DropdownOption(key="0007", text="Thetford"),
                    ft.DropdownOption(key="3005", text="Caerleon"),
                    ft.DropdownOption(key="5003", text="Brecilien"),
                ],
                on_select=lambda _: self.trigger_save(),
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
            col={"sm": 0.6}, alignment=ft.Alignment.CENTER,
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
            alignment=ft.Alignment.CENTER,
            content=ft.Icon(icon=COMMAND_TYPES[function_type]["icon"], color="#ffffff"),
        )

        self.remove_btn_container = ft.Container(
            content=ft.IconButton(icon=ft.Icons.DELETE, icon_color=GuiStyle.Colors.ACCENT_RED),
            col={"sm": 1},
            alignment=ft.Alignment.CENTER_RIGHT,
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
                self.remove_btn_container,
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
            new_func = FunctionToExecute(
                func_type,
                can_be_removed=True,
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
            function.content.controls[1] = function.remove_btn_container

        try:
            self.update()
        except RuntimeError:
            pass


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
            padding=ft.Padding.symmetric(vertical=15, horizontal=10),
            border_radius=10,
            border=ft.Border.all(1, "#1e293b"),
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

        self.run_warning = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=GuiStyle.Colors.ACCENT_RED, size=20),
                    ft.Text(
                        "Change location to initialize Travel",
                        color=GuiStyle.Colors.ACCENT_RED,
                        weight=ft.FontWeight.BOLD,
                        size=14
                    )
                ],
                alignment=ft.MainAxisAlignment.END,
            ),
            padding=ft.Padding.only(right=10),
            col={"sm": 7, "md": 8.5, "xl": 9.55},
            visible=False
        )

        self.bgcolor = GuiStyle.Colors.CARD_BG
        self.padding = ft.Padding.only(left=20, top=15, right=20, bottom=20)
        self.border_radius = 15
        self.border = ft.Border.all(1, GuiStyle.Colors.BORDER_DEFAULT)
        self.content = ft.Column(
            controls=[
                ft.ResponsiveRow(
                    controls=[
                        title,
                        # self.home_island,
                    ],
                    vertical_alignment=ft.VerticalAlignment.CENTER,
                ),
                ft.Divider(color=GuiStyle.Colors.BORDER_DEFAULT),
                self.execution_functions_list,
                ft.Divider(color=GuiStyle.Colors.BORDER_DEFAULT),
                ft.Container(
                    content=self.lower_row, padding=ft.Padding.only(left=0, top=0, right=0, bottom=10)
                ),
                ft.ResponsiveRow(
                    controls=[self.run_warning, self.run_button], alignment=ft.MainAxisAlignment.END,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
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
        self.padding = ft.Padding.only(left=0, top=10, right=0, bottom=0)

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
        self.alignment = ft.Alignment.CENTER
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
                    content=ft.Text("Go to Shop"),
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
            padding=ft.Padding.only(left=0, top=0, right=0, bottom=10),
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
            padding=ft.Padding.only(left=20, top=10, right=20, bottom=0),
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

            try:
                self.update()
            except RuntimeError:
                pass


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
                padding=ft.Padding.all(20),
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
            alignment=ft.Alignment.CENTER,
            padding=5,
            border=ft.Border.all(1, GuiStyle.Colors.BORDER_DEFAULT)
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
                    padding=ft.Padding.symmetric(horizontal=5, vertical=2),
                    border_radius=3,
                    width=70,
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Text(message, size=13, font_family="monospace", expand=True),
            ]

    def __init__(self, initial_logs=None):
        super().__init__()
        self.padding = 10
        self.border = ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)
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
            padding=ft.Padding.only(left=0, top=0, right=0, bottom=10),
        )

        self.logs_list_content = ft.Column(
            controls=[], spacing=10  # Populated dynamically
        )

        self.logs_view = LogsView()
        self.logs_view.visible = False
        self.logs_view.margin = ft.Margin.only(left=0, top=10, right=0, bottom=20)

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
        try:
            self.update()
        except RuntimeError:
            pass

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


#========================================
# PRICES DISPLAY PART
#========================================
class ItemData:
    """Helper class to parse item data for filtering."""
    def __init__(self, unique_name, localized_name, category, sub_category):
        self.unique_name = unique_name
        self.localized_name = localized_name
        self.category = category
        self.sub_category = sub_category
        match = re.match(r"T(\d+)_", unique_name)
        self.tier = int(match.group(1)) if match else 0
        if "@" in unique_name:
            try:
                self.enchant = int(unique_name.split("@")[1])
            except:
                self.enchant = 0
        else:
            self.enchant = 0


class MarketTable(ft.Column):
    def __init__(self, dashboard: "Dashboard"):
        super().__init__()
        self.dashboard = dashboard
        self.spacing = 10
        self.all_items = []
        self.filtered_items = []
        self.page_number = 1
        self.items_per_page = 15

        # Price Cache
        self.price_cache_fast = {}
        self.price_cache_order = {}
        self.is_loading_prices = False

        # Filters state
        self.selected_cat = None
        self.selected_sub = None
        self.selected_tiers = set()
        self.selected_enchants = set()

        self._init_ui()
        self._load_items_data()

    def _create_chip(self, text, data, callback):
        """Helper method to create consistent filter chips."""
        return ft.Chip(
            label=ft.Text(text, size=11, color=GuiStyle.Colors.WHITE),
            on_select=callback,
            data=data,
            label_padding=ft.padding.Padding.symmetric(horizontal=4),
            bgcolor=GuiStyle.Colors.INNER_BG,
            border_side=ft.BorderSide(width=0, color=ft.Colors.TRANSPARENT),
            selected_color=GuiStyle.Colors.DARK_BLUE,
        )

    def _init_ui(self):
        def create_chip(text, data, callback):
            return ft.Chip(
                label=ft.Text(text, size=11, color=GuiStyle.Colors.WHITE),
                on_select=callback,
                data=data,
                label_padding=ft.padding.Padding.symmetric(horizontal=4),
                bgcolor=GuiStyle.Colors.INNER_BG,
                border_side=ft.BorderSide(width=0, color=ft.Colors.TRANSPARENT),
                selected_color=GuiStyle.Colors.DARK_BLUE,
            )

        self.search_input = ft.TextField(
            label="Search by name...",
            suffix_icon=ft.Icons.SEARCH,
            text_size=12,
            dense=True,
            height=35,
            expand=True,
            on_change=lambda e: self.apply_filters(),
            bgcolor=GuiStyle.Colors.DARK_BLUE,
            color=GuiStyle.Colors.TEXT_PRIMARY,
        )

        # FIXED: Replaced 'text=' with 'content=ft.Text(...)'
        self.refresh_prices_btn = ft.TextButton(
            content=ft.Text("Refresh Prices"),
            icon=ft.Icons.REFRESH_ROUNDED,
            on_click=lambda _: threading.Thread(
                target=self.refresh_all_prices, daemon=True
            ).start(),
            style=ft.ButtonStyle(color=GuiStyle.Colors.TEXT_PRIMARY),
        )

        header_row = ft.Row(
            controls=[self.search_input, self.refresh_prices_btn],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )

        self.cat_row = ft.Row(wrap=True, spacing=2, run_spacing=2)
        self.sub_row = ft.Row(wrap=True, spacing=2, run_spacing=2)

        self.tier_row = ft.Row(
            wrap=True,
            spacing=2,
            run_spacing=2,
            controls=[
                create_chip(f"T{t}", t, self.on_tier_toggle) for t in [4, 5, 6, 7, 8]
            ],
        )
        self.enchant_row = ft.Row(
            wrap=True,
            spacing=2,
            run_spacing=2,
            controls=[
                create_chip(f".{e}", e, self.on_enchant_toggle) for e in [0, 1, 2, 3, 4]
            ],
        )

        def remove_filters(e):
            self.selected_cat = None
            self.selected_sub = None
            self.selected_tiers.clear()
            self.selected_enchants.clear()
            self.search_input.value = ""
            for chip in self.cat_row.controls:
                chip.selected = False
            for chip in self.tier_row.controls:
                chip.selected = False
            for chip in self.enchant_row.controls:
                chip.selected = False
            self.sub_row.controls.clear()

            try:
                self.cat_row.update()
                self.sub_row.update()
                self.tier_row.update()
                self.enchant_row.update()
                self.search_input.update()
            except RuntimeError:
                pass

            self.apply_filters()

        def header_cell(text):
            return ft.Container(
                content=ft.Text(text, weight="bold", size=12),
                padding=ft.padding.Padding.symmetric(vertical=10, horizontal=5),
                margin=ft.margin.Margin.only(top=1, left=2, right=2),
            )

        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(header_cell("Image")),
                ft.DataColumn(header_cell("Item Name")),
                ft.DataColumn(header_cell("BM Order Price")),
                ft.DataColumn(header_cell("BM Fast Price")),
                ft.DataColumn(header_cell("Last Update")),
            ],
            heading_row_color=GuiStyle.Colors.CARD_BG,
            data_row_color={ft.ControlState.HOVERED: "#2A3C55"},
            column_spacing=10,
            heading_row_height=50,
            width=float("inf"),
        )

        self.table_container = ft.Container(
            content=self.data_table,
            bgcolor=GuiStyle.Colors.CARD_BG,
            border_radius=10,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            border=ft.border.Border.all(2, GuiStyle.Colors.BORDER_DEFAULT),
            padding=0,
        )

        # FIXED: Explicit 'icon=' parameters for IconButton
        self.prev_btn = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            on_click=lambda e: self.change_page(-1),
            disabled=True,
        )
        self.next_btn = ft.IconButton(
            icon=ft.Icons.ARROW_FORWARD,
            on_click=lambda e: self.change_page(1),
            disabled=True,
        )
        self.page_info = ft.Text("Page 1", color=GuiStyle.Colors.WHITE)

        self.pagination_row = ft.Row(
            [self.prev_btn, self.page_info, self.next_btn],
            alignment=ft.MainAxisAlignment.CENTER,
        )

        filter_panel = ft.Container(
            content=ft.ResponsiveRow(
                controls=[
                    ft.Column(
                        controls=[
                            header_row,
                            ft.Row(
                                [
                                    ft.Text("Tier:", size=11, color="#ffffff"),
                                    self.tier_row,
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Row(
                                [
                                    ft.Text("Ench:", size=11, color="#ffffff"),
                                    self.enchant_row,
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ],
                        col={"md": 4},
                    ),
                    ft.Column(
                        controls=[
                            ft.Column(
                                [
                                    ft.Text("Category:", size=11, color="#ffffff"),
                                    self.cat_row,
                                ],
                                spacing=0,
                            ),
                            ft.Column(
                                [
                                    ft.Text("Sub-Category:", size=11, color="#ffffff"),
                                    self.sub_row,
                                ],
                                spacing=0,
                            ),
                        ],
                        spacing=2,
                        col={"md": 7},
                    ),
                    ft.Column(
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.REFRESH_ROUNDED,
                                icon_color=ft.Colors.WHITE,
                                tooltip="Remove Filters",
                                on_click=remove_filters,
                            )
                        ],
                        spacing=2,
                        col={"md": 0.5},
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=5,
            bgcolor=GuiStyle.Colors.CARD_BG,
            border_radius=5,
            border=ft.border.Border.all(1, GuiStyle.Colors.BORDER_DEFAULT),
        )

        self.controls = [
            ft.Text(
                "Black Market Prices",
                size=20,
                weight="bold",
                color=GuiStyle.Colors.TEXT_PRIMARY,
            ),
            filter_panel,
            self.table_container,
            self.pagination_row,
        ]

    def _load_items_data(self):
        """Loads item definitions and triggers the one-time price fetch."""
        path = self.dashboard.config.BOT_ITEMS_FILE
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.all_items = []
            categories = []
            for cat, sub_cats in data.items():
                categories.append(cat)
                for sub, items in sub_cats.items():
                    if isinstance(items, dict):
                        for uid, name in items.items():
                            self.all_items.append(ItemData(uid, name, cat, sub))
                    elif isinstance(items, list):
                        for uid in items:
                            self.all_items.append(ItemData(uid, uid, cat, sub))

            self.cat_row.controls = [
                self._create_chip(c, c, self.on_cat_toggle) for c in categories
            ]

            threading.Thread(target=self.refresh_all_prices, daemon=True).start()

            self.apply_filters()
        except Exception as e:
            print(f"Error loading items: {e}")

    def refresh_all_prices(self):
        """Fetches prices for all items for the server to populate the cache once."""
        if self.is_loading_prices:
            return
        self.is_loading_prices = True

        try:
            server = self.dashboard.config.get("general").get("server", "US")

            res_fast = requests.get(
                f"{self.dashboard.API_URL}/items/",
                params={"cities": ["black_market"], "type": "order", "server": server},
            )
            if res_fast.status_code == 200:
                for x in res_fast.json():
                    self.price_cache_fast[x["unique_name"]] = x

            res_order = requests.get(
                f"{self.dashboard.API_URL}/items/",
                params={"cities": ["black_market"], "type": "fast", "server": server},
            )
            if res_order.status_code == 200:
                for x in res_order.json():
                    self.price_cache_order[x["unique_name"]] = x

            self.render_table()

        except Exception as e:
            print(f"Error fetching prices: {e}")

        self.is_loading_prices = False

    def render_table(self):
        """Renders the table immediately using the cached data."""
        max_page = math.ceil(len(self.filtered_items) / self.items_per_page) or 1
        if self.page_number > max_page:
            self.page_number = max_page
        if self.page_number < 1:
            self.page_number = 1

        self.page_info.value = f"Page {self.page_number} / {max_page}"
        self.prev_btn.disabled = self.page_number <= 1
        self.next_btn.disabled = self.page_number >= max_page

        start = (self.page_number - 1) * self.items_per_page
        end = start + self.items_per_page
        page_items = self.filtered_items[start:end]

        rows = []
        for item in page_items:
            f_info = self.price_cache_fast.get(item.unique_name, {})
            o_info = self.price_cache_order.get(item.unique_name, {})

            p_fast_raw = f_info.get("price_black_market")
            p_order_raw = o_info.get("price_black_market")

            price_fast = (
                f"{int(p_fast_raw/10000):,}" if p_fast_raw else "No Data"
            )
            price_order = (
                f"{int(p_order_raw/10000):,}" if p_order_raw else "No Data"
            )

            t_fast = f_info.get("black_market_updated_at")
            t_order = o_info.get("black_market_updated_at")
            last_update_str = "-"
            valid_times = [t for t in [t_fast, t_order] if t]
            if valid_times:
                best_time = max(valid_times)
                try:
                    dt = datetime.fromisoformat(best_time.replace("Z", "+00:00"))
                    now = datetime.now(dt.tzinfo)
                    diff = now - dt
                    if diff.days > 0:
                        last_update_str = f"{diff.days}d ago"
                    elif diff.seconds > 3600:
                        last_update_str = f"{diff.seconds // 3600}h ago"
                    elif diff.seconds > 60:
                        last_update_str = f"{diff.seconds // 60}m ago"
                    else:
                        last_update_str = "Just now"
                except Exception:
                    last_update_str = "Unknown"

            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Image(
                                src=f"https://render.albiononline.com/v1/item/{item.unique_name}",
                                width=40,
                                height=40,
                                fit=ft.ImageFit.CONTAIN,
                                border_radius=5,
                            )
                        ),
                        ft.DataCell(
                            ft.Text(item.localized_name, weight="bold", color="white")
                        ),
                        ft.DataCell(
                            ft.Text(
                                str(price_order),
                                color=GuiStyle.Colors.ACCENT_GREEN,
                                weight=ft.FontWeight.BOLD,
                            )
                        ),
                        ft.DataCell(
                            ft.Text(
                                str(price_fast),
                                color=GuiStyle.Colors.ACCENT_ORANGE,
                                weight=ft.FontWeight.BOLD,
                            )
                        ),
                        ft.DataCell(
                            ft.Text(last_update_str, color="white70")
                        ),
                    ]
                )
            )

        self.data_table.rows = rows
        try:
            self.pagination_row.update()
            self.data_table.update()
        except RuntimeError:
            pass

    def on_cat_toggle(self, e):
        self.selected_cat = e.control.data if e.control.selected else None
        for chip in self.cat_row.controls:
            chip.selected = chip.data == self.selected_cat
        try:
            self.cat_row.update()
        except RuntimeError:
            pass

        self.sub_row.controls.clear()
        self.selected_sub = None
        if self.selected_cat:
            subs = sorted(
                list(
                    set(
                        i.sub_category
                        for i in self.all_items
                        if i.category == self.selected_cat
                    )
                )
            )

            def create_chip(text, data, callback):
                return ft.Chip(
                    label=ft.Text(text, size=11, color="white"),
                    on_select=callback,
                    data=data,
                    label_padding=ft.padding.symmetric(horizontal=4),
                    bgcolor=GuiStyle.Colors.INNER_BG,
                    border_side=ft.BorderSide(
                        width=0, color=ft.Colors.TRANSPARENT
                    ),
                    selected_color=GuiStyle.Colors.DARK_BLUE,
                )

            for s in subs:
                self.sub_row.controls.append(create_chip(s, s, self.on_sub_toggle))

        try:
            self.sub_row.update()
        except RuntimeError:
            pass

        self.apply_filters()

    def on_sub_toggle(self, e):
        self.selected_sub = e.control.data if e.control.selected else None
        for chip in self.sub_row.controls:
            chip.selected = chip.data == self.selected_sub

        try:
            self.sub_row.update()
        except RuntimeError:
            pass

        self.apply_filters()

    def on_tier_toggle(self, e):
        t = e.control.data
        if e.control.selected:
            self.selected_tiers.add(t)
        else:
            self.selected_tiers.discard(t)
        self.apply_filters()

    def on_enchant_toggle(self, e):
        en = e.control.data
        if e.control.selected:
            self.selected_enchants.add(en)
        else:
            self.selected_enchants.discard(en)
        self.apply_filters()

    def apply_filters(self):
        search_term = (
            self.search_input.value.lower() if self.search_input.value else ""
        )
        res = []
        for item in self.all_items:
            if self.selected_cat and item.category != self.selected_cat:
                continue
            if self.selected_sub and item.sub_category != self.selected_sub:
                continue
            if self.selected_tiers and item.tier not in self.selected_tiers:
                continue
            if self.selected_enchants and item.enchant not in self.selected_enchants:
                continue
            if search_term and not (
                search_term in item.localized_name.lower()
                or search_term in item.unique_name.lower()
            ):
                continue
            res.append(item)
        self.filtered_items = res
        self.page_number = 1
        self.render_table()

    def change_page(self, delta):
        new_page = self.page_number + delta
        max_page = math.ceil(len(self.filtered_items) / self.items_per_page) or 1
        if 1 <= new_page <= max_page:
            self.page_number = new_page
            self.render_table()






class Dashboard(ft.Container):
    def __init__(
        self,
        app: "GuiApp",
        config: SettingsHandler,
        page,
        bot: "Bot",
        header=None,
        login=None,
    ):
        super().__init__()
        self.expand = True
        self.app = app
        self.config = config
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

        self.dashboard_panel.orders_graph.update_graph_data()

        self.bot.sniffer.subscribe_location(self.dashboard_panel.overview_panel._get_data_background)
        self.bot.sniffer.subscribe_location(self.check_start_requirements)

        self.seq_panel = (
            self.bot_sequence_panel.bot_control_panel.execution_sequence_panel
        )
        self.avail_panel = (
            self.bot_sequence_panel.bot_control_panel.functions_avaliable_panel
        )

        self.seq_panel.execution_functions_list.load_sequence(self.bot_sequence)
        self.check_start_requirements()

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

    def check_start_requirements(self, *args):
        has_travel = False
        if self.bot_sequence:
            for item in self.bot_sequence:
                if item.get("type") == "travel_to":
                    has_travel = True
                    break
        
        location_id = ""
        if self.bot and self.bot.local_player and self.bot.local_player.location:
             location_id = self.bot.local_player.location.location_id
        
        should_block = has_travel and (location_id == "")
        
        if self.bot_sequence_panel:
            panel = self.bot_sequence_panel.bot_control_panel.execution_sequence_panel
            
            if not self.is_running_sequence:
                panel.run_button.disabled = should_block
                panel.run_warning.visible = should_block
                try:
                    panel.update()
                except RuntimeError:
                    pass

    def save_sequence(self):
        self.bot_sequence = [
            c.get_serialized_data()
            for c in self.seq_panel.execution_functions_list.content.controls
        ]
        if self.config:
            self.config.save_bot_loop(self.bot_sequence)
        self.check_start_requirements()

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
            self.bot._stop_requested = False
            self.bot.resume()
            while self.is_running_sequence:
                for item in self.bot_sequence:
                    if not self.is_running_sequence: break
                    if not self.bot: break
                    

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
            self.dashboard_panel.orders_graph.update_graph_data()
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
