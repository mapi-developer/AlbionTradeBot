import flet as ft
import multiprocessing
import time
import os

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
        page.window.width = 280
        page.window.height = 110
        page.window.skip_task_bar = True

        status_text = ft.Text("BOT ACTIVE", color=ft.Colors.GREEN_ACCENT, weight="bold", size=16)
        task_text = ft.Text("Waiting...", color=ft.Colors.WHITE, size=13)

        page.add(
            ft.Container(
                content=ft.Column([status_text, task_text], spacing=5),
                bgcolor="#CC131415",
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
                        status_text.color = ft.Colors.ORANGE_400 if data.get('paused') else ft.Colors.GREEN_400
                
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

    def start(self):
        if self.process and self.process.is_alive():
            return
        # Ensure the process is created safely
        self.process = multiprocessing.Process(target=run_flet_overlay, args=(self.status_queue,), daemon=True)
        self.process.start()

    def stop(self):
        if self.process and self.process.is_alive():
            try:
                # Clear queue and send stop signal
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

    def send_update(self, status, task, paused):
        if self.process and self.process.is_alive():
            try:
                self.status_queue.put_nowait({"status": status, "task": task, "paused": paused})
            except:
                pass