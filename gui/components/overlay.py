import flet as ft
import multiprocessing
import asyncio
import os, sys
import ctypes

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.components.style import GuiStyle

def get_asset_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def get_active_window_title():
    """Returns the title of the currently active (foreground) window."""
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value
    except Exception:
        return ""

def run_flet_overlay(status_queue):
    # Clear Flet environment variables to avoid process port inheritance issues
    os.environ.pop("FLET_SERVER_PORT", None)
    os.environ.pop("FLET_SERVER_IP", None)
    os.environ.pop("FLET_DISPLAY_URL", None)

    async def overlay_main(page: ft.Page):
        # Configure frameless & transparent window properties
        page.window.title_bar_hidden = True
        page.window.frameless = True
        page.window.always_on_top = True
        page.window.bgcolor = ft.Colors.TRANSPARENT
        page.bgcolor = ft.Colors.TRANSPARENT
        page.window.width = 350
        page.window.height = 250
        page.window.skip_task_bar = True

        status_text = ft.Text("BOT ACTIVE", color=ft.Colors.GREEN_ACCENT, weight="bold", size=14)
        task_text = ft.Text("Waiting...", color=ft.Colors.WHITE, size=12)
        
        # Container for the list of items
        items_column = ft.Column(spacing=2)

        page.add(
            ft.Container(
                content=ft.Column([
                    status_text, 
                    task_text,
                    ft.Divider(height=1, color=ft.Colors.WHITE_24),
                    items_column
                ], spacing=5),
                bgcolor="#CC131415",  # Semi-transparent dark background
                padding=15,
                border_radius=10,
                border=ft.Border.all(1, "#294D7C")
            )
        )

        page.update()

        # Non-blocking async UI loop
        while True:
            try:
                active_title = get_active_window_title()

                # Toggle visibility based on active window
                if "Market Trader" in active_title:
                    if page.window.visible:
                        page.window.visible = False
                        page.update()
                else:
                    if not page.window.visible:
                        page.window.visible = True
                        page.update()

                # Process status updates from main process queue
                if not status_queue.empty():
                    data = status_queue.get_nowait()
                    
                    if data == "STOP":
                        await page.window.destroy()
                        return

                    if isinstance(data, dict):
                        status = data.get('status', '')
                        if status.lower() == 'running':
                            status_text.value = f"STATUS: {status.upper()} Press F1 to Pause"
                        else:
                            status_text.value = f"STATUS: {status.upper()} Press F1 to Resume"
                        
                        task_text.value = data.get('task', '')
                        status_text.color = GuiStyle.Colors.ACCENT_ORANGE if data.get('paused') else GuiStyle.Colors.ACCENT_GREEN
                        
                        # Update Recent Items List
                        recent_items = data.get('recent_items', [])
                        items_column.controls.clear()
                        for item in recent_items:
                            if isinstance(item, dict):
                                price_color = ft.Colors.GREEN_ACCENT if item.get('type') == 'buy' else GuiStyle.Colors.ACCENT_BLUE
                                items_column.controls.append(
                                    ft.Row([
                                        ft.Text(item.get('name'), size=11, color=ft.Colors.WHITE, overflow=ft.TextOverflow.ELLIPSIS, width=150, no_wrap=True),
                                        ft.Text(item.get('price'), size=11, color=price_color, weight="bold"),
                                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                                )
                
                page.update()
            except Exception:
                break
                
            await asyncio.sleep(0.3)

    ft.app(target=overlay_main, assets_dir=get_asset_path("assets"))


class BotOverlay:
    def __init__(self):
        self.status_queue = multiprocessing.Queue()
        self.process = None
        self.last_items = []  # Cache to store items between status updates

    def start(self):
        self.last_items = []
        if self.process and self.process.is_alive():
            return
        self.process = multiprocessing.Process(target=run_flet_overlay, args=(self.status_queue,), daemon=True)
        self.process.start()

    def stop(self):
        self.last_items = []
        if self.process and self.process.is_alive():
            try:
                while not self.status_queue.empty():
                    self.status_queue.get_nowait()
                
                self.status_queue.put("STOP")
                self.process.join(timeout=1.0)
                
                if self.process.is_alive():
                    self.process.terminate()
            except Exception as e:
                print(f"Error stopping overlay: {e}")
            finally:
                self.process = None

    def send_update(self, status, task, paused, recent_items=None):
        if recent_items is not None:
            self.last_items = recent_items

        if self.process and self.process.is_alive():
            try:
                self.status_queue.put_nowait({
                    "status": status, 
                    "task": task, 
                    "paused": paused,
                    "recent_items": self.last_items
                })
            except Exception:
                pass