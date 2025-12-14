import flet as ft
from gui.app import main as gui_main
import traceback

def main():
    try:
        ft.app(target=gui_main)
    except Exception:
        # Log unexpected crashes to a file next to the exe
        error_path = "crash_log.txt"
        with open(error_path, "w") as f:
            f.write(traceback.format_exc())

if __name__ == "__main__":
    main()