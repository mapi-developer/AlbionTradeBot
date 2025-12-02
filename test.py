import flet as ft
import sys
import threading
import io
import time
from bot import TradeBot
from database.interface import DatabaseInterface

class ConsoleRedirector(io.StringIO):
    def __init__(self, update_callback):
        super().__init__()
        self.update_callback = update_callback

    def write(self, message):
        if message.strip():
            self.update_callback(message)

    def flush(self):
        pass

def main(page: ft.Page):
    # --- App Configuration ---
    page.title = "Albion Trade Bot GUI"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 600
    page.window_height = 700
    page.padding = 20

    # --- UI Elements ---
    
    header = ft.Text("Albion Trade Bot", size=30, weight=ft.FontWeight.BOLD)
    # Fixed: Use ft.Colors (Uppercase)
    status_text = ft.Text("Status: Ready", color=ft.Colors.GREEN)

    # Log/Console Output Area
    log_output = ft.TextField(
        value="--- Bot Logs will appear here ---\n",
        multiline=True,
        read_only=True,
        text_size=12,
        expand=True,
        bgcolor=ft.Colors.BLACK38,      # Fixed: Use bgcolor for background
        border_color=ft.Colors.GREY_800, # Fixed: Use ft.Colors
    )

    autoscroll_check = ft.Checkbox(label="Auto-scroll logs", value=True)

    bot_instance = None

    # --- Logic Functions ---

    def log_message(message):
        current_val = log_output.value or ""
        log_output.value = current_val + message
        page.update()

    sys.stdout = ConsoleRedirector(log_message)
    sys.stderr = ConsoleRedirector(log_message)

    def init_bot():
        nonlocal bot_instance
        if bot_instance is None:
            log_message("[GUI] Initializing Database & Bot...\n")
            try:
                db = DatabaseInterface()
                bot_instance = TradeBot(db=db)
                log_message("[GUI] Bot Initialized Successfully.\n")
                return True
            except Exception as e:
                log_message(f"[GUI] Error Initializing Bot: {e}\n")
                log_message("[GUI] Ensure Docker is running.\n")
                return False
        return True

    def run_check_price(e):
        if not init_bot(): return

        start_btn.disabled = True
        buy_btn.disabled = True
        status_text.value = "Status: Checking Prices..."
        status_text.color = ft.Colors.ORANGE # Fixed: ft.Colors
        page.update()

        def task():
            try:
                log_message("\n--- Starting Price Check ---\n")
                bot_instance.check_price()
                log_message("\n--- Price Check Complete ---\n")
            except Exception as ex:
                log_message(f"\n[Error] {ex}\n")
            finally:
                start_btn.disabled = False
                buy_btn.disabled = False
                status_text.value = "Status: Ready"
                status_text.color = ft.Colors.GREEN
                page.update()

        threading.Thread(target=task, daemon=True).start()

    def run_buy_items(e):
        if not init_bot(): return

        start_btn.disabled = True
        buy_btn.disabled = True
        status_text.value = "Status: Buying Items..."
        status_text.color = ft.Colors.BLUE # Fixed: ft.Colors
        page.update()

        def task():
            try:
                log_message("\n--- Starting Buy Routine ---\n")
                bot_instance.buy_items()
                log_message("\n--- Buy Routine Complete ---\n")
            except Exception as ex:
                log_message(f"\n[Error] {ex}\n")
            finally:
                start_btn.disabled = False
                buy_btn.disabled = False
                status_text.value = "Status: Ready"
                status_text.color = ft.Colors.GREEN
                page.update()

    # --- Buttons ---
    start_btn = ft.ElevatedButton(
        "Check Black Market Prices", 
        icon=ft.Icons.SEARCH, 
        on_click=run_check_price,
        bgcolor=ft.Colors.INDIGO_600, # Fixed: ft.Colors
        color=ft.Colors.WHITE         # Fixed: ft.Colors
    )

    buy_btn = ft.ElevatedButton(
        "Buy Items", 
        icon=ft.Icons.SHOPPING_CART, 
        on_click=run_buy_items,
        bgcolor=ft.Colors.TEAL_600,   # Fixed: ft.Colors
        color=ft.Colors.WHITE         # Fixed: ft.Colors
    )

    # --- Layout ---
    page.add(
        header,
        status_text,
        ft.Divider(),
        ft.Row([start_btn, buy_btn], alignment=ft.MainAxisAlignment.START),
        ft.Divider(),
        ft.Text("Console Output:", size=14, color=ft.Colors.GREY_400),
        ft.Container(
            content=log_output,
            expand=True,
            border_radius=10,
        ),
        autoscroll_check
    )

if __name__ == "__main__":
    ft.app(target=main)