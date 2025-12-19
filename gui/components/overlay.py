import flet as ft
import multiprocessing
import time

def run_flet_overlay(status_queue):
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
                    
                    # 1. Graceful Shutdown Signal
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

    ft.app(target=overlay_main)

class BotOverlay:
    def __init__(self):
        self.status_queue = multiprocessing.Queue()
        self.process = None

    def start(self):
        if self.process and self.process.is_alive():
            return
        self.process = multiprocessing.Process(target=run_flet_overlay, args=(self.status_queue,), daemon=True)
        self.process.start()

    def stop(self):
        """Forces the overlay to close and clears any pending updates."""
        if self.process and self.process.is_alive():
            try:
                # 1. Clear the queue so the process doesn't try to process old data
                while not self.status_queue.empty():
                    self.status_queue.get_nowait()
                
                # 2. Send the poison pill
                self.status_queue.put("STOP")
                
                # 3. Give it a tiny moment to self-destruct
                self.process.join(timeout=0.2)
                
                # 4. If it's still stubborn, kill it
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