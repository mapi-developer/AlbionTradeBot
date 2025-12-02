import asyncio
import flet as ft

class Popup:
    """
    Handles displaying success and error notifications using a custom top-center banner.
    """
    _notification_banner = None

    @staticmethod
    def init_popup(page: ft.Page) -> ft.Container:
        """
        Initializes the notification banner.
        Returns the banner control to be added to the page layout.
        """
        Popup._notification_banner = ft.Container(
            content=ft.Row(
                [ft.Text(expand=True, text_align=ft.TextAlign.CENTER)],
                alignment=ft.MainAxisAlignment.CENTER
            ),
            bgcolor=ft.Colors.GREEN,
            width=400,
            height=50,
            padding=15,
            border_radius=10,
            top=-100,  # Start off-screen,
            alignment=ft.alignment.center,
            animate_position=ft.Animation(300, "easeOut"),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
                offset=ft.Offset(0, 5),
            )
        )
        return Popup._notification_banner

    async def _show_banner(page: ft.Page, message: str, color: str, duration_ms: int):
        if not page or not Popup._notification_banner:
            return

        banner = Popup._notification_banner
        banner.content.controls[0].value = message
        banner.bgcolor = color
        banner.top = 20  # Animate in
        await page.update_async()

        await asyncio.sleep(duration_ms / 1000)

        banner.top = -100  # Animate out
        await page.update_async()

    @staticmethod
    def show_success(page: ft.Page, message: str):
        asyncio.run_coroutine_threadsafe(Popup._show_banner(page, message, ft.Colors.GREEN_700, 2000), page.loop)

    @staticmethod
    def show_error(page: ft.Page, message: str):
        asyncio.run_coroutine_threadsafe(Popup._show_banner(page, message, ft.Colors.RED_700, 3000), page.loop)
