import flet as ft
import time

class LeftPanelButton(ft.Container):
    def __init__(self, text: str, data: str):
        super().__init__()
        self.padding = 0
        self.col = {"sm": 12, "md": 12, "xl": 12}
        self.content = ft.ElevatedButton(
            text=text,
            data=data,
            # on_click=on_tab_change,
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

        self.upper_buttons = ft.Column(
            spacing=0,
            controls=[
                ft.ResponsiveRow(
                    spacing=0,
                    run_spacing=0,
                    controls=[
                        LeftPanelButton("Dashboard", "dashboard"),
                        LeftPanelButton("Bot Sequence", "sequence"),
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
                    controls=[LeftPanelButton("Activity Logs", "logs")],
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

        self.last_prices_update = InfoCard(title="Last Prices Update (UTC)", icon=ft.Icons.UPDATE)
        self.database_status = InfoCard(title="Database Status", icon=ft.Icons.ACCOUNT_TREE)
        self.bot_status = InfoCard(title="Bot Status", icon=ft.Icons.ADB)
        self.subscribed_until = InfoCard(title="Subscribed until", icon=ft.Icons.ADD_TASK)

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
                    ft.ChartAxisLabel(value=int(max_y/2), label=ft.Text(str(int(max_y/2)), size=15)),
                    ft.ChartAxisLabel(value=max_y, label=ft.Text(str(max_y), size=15)),
                ],
                labels_size=30,
            ),
            border=ft.border.all(3, ft.Colors.with_opacity(0.5, ft.Colors.ON_SURFACE)),
            tooltip_bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLUE_GREY_800),
            horizontal_grid_lines=ft.ChartGridLines(
                interval=max_y/4, color=ft.Colors.with_opacity(0.2, ft.Colors.ON_SURFACE), width=1
            ),
            vertical_grid_lines=ft.ChartGridLines(
                interval=1, color=ft.Colors.with_opacity(0.2, ft.Colors.ON_SURFACE), width=1
            ),
            min_y=0,
            max_y=max_y,
            expand=True,
        )

        self.content = ft.Column([
            ft.Text("Order Activity (Last 3 Days)", size=16, weight=ft.FontWeight.BOLD),
            ft.Container(content=self.chart, height=300) 
        ])


class RightPanel(ft.Column):
    def __init__(self, content_controls = []):
        super().__init__()

        self.col = {"sm": 10.5, "md": 10.5, "xl": 10.5}
        self.controls = [
            ft.Container(
                content=ft.Column(
                    spacing=0,
                    controls=content_controls
                ),
                bgcolor=ft.Colors.TRANSPARENT,
                padding=ft.padding.only(20, 10, 20, 0),
            )
        ]
        

class DashboardPanel(RightPanel):
    def __init__(self):
        self.overview_panel = OverviewPanel()
        self.orders_graph = OrdersGraph()
        super().__init__(
            content_controls=[
                ft.Divider(),
                self.overview_panel,
                ft.Divider(),
                self.orders_graph
            ]
        )


class Dashboard(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.left_panel = LeftPanel()
        self.dashboard_panel = DashboardPanel()
        self.content = ft.ResponsiveRow(
            controls=[self.left_panel, self.dashboard_panel], spacing=0
        )


def main(page: ft.Page):
    page.padding = 0
    page.title = "Dashboard"
    page.expand = True

    dashboard = Dashboard()

    page.add(dashboard)
    dashboard.dashboard_panel.overview_panel.subscribed_until.update_data("Data Updated")
    page.update()


if __name__ == "__main__":
    ft.app(target=main)
