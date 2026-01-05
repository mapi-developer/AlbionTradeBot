import flet as ft
import multiprocessing
import time
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.components.style import GuiStyle

def run_flet_overlay(status_queue):
    os.environ.pop("FLET_SERVER_PORT", None)
    os.environ.pop("FLET_SERVER_IP", None)
    os.environ.pop("FLET_DISPLAY_URL", None)

    def overlay_main(page: ft.Page):
        page.window.title_bar_hidden = True
        page.window.frameless = True
        page.window.always_on_top = True
        page.window.bgcolor = ft.Colors.TRANSPARENT
        page.bgcolor = ft.Colors.TRANSPARENT
        page.window.width = 350
        page.window.height = 250  # Increased height for list
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
                    ft.Divider(height=1, color=ft.Colors.WHITE24),
                    items_column
                ], spacing=5),
                bgcolor="#CC131415", # Semi-transparent dark
                padding=15,
                border_radius=10,
                border=ft.border.all(1, "#294D7C")
            )
        )

        while True:
            try:
                if not status_queue.empty():
                    data = status_queue.get_nowait()
                    
                    if data == "STOP":
                        page.window.destroy()
                        return

                    if isinstance(data, dict):
                        status_text.value = f"STATUS: {data.get('status', '').upper()}"
                        task_text.value = data.get('task', '')
                        status_text.color = GuiStyle.Colors.ACCENT_ORANGE if data.get('paused') else GuiStyle.Colors.ACCENT_GREEN
                        
                        # Update Recent Items List
                        recent_items = data.get('recent_items', [])
                        items_column.controls.clear()
                        for item in recent_items:
                             # item is a dict {name, price, type}
                             if isinstance(item, dict):
                                 price_color = ft.Colors.GREEN_ACCENT if item.get('type') == 'buy' else GuiStyle.Colors.ACCENT_BLUE
                                 items_column.controls.append(
                                     ft.Row([
                                         ft.Text(item.get('name'), size=11, color=ft.Colors.WHITE, overflow=ft.TextOverflow.ELLIPSIS, width=150, no_wrap=True),
                                         ft.Text(item.get('price'), size=11, color=price_color, weight="bold"),
                                     ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                                 )
                
                page.update()
            except:
                break
            time.sleep(0.3)

    # Use port=0 to allow the OS to pick any available port, avoiding conflicts
    ft.app(target=overlay_main, port=0, host="127.0.0.1", view=ft.AppView.FLET_APP)

class BotOverlay:
    def __init__(self):
        self.status_queue = multiprocessing.Queue()
        self.process = None
        self.last_items = [] # Cache to store items between status updates

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
                self.process.join(timeout=1.0) # Increase timeout slightly
                
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
            except:
                pass