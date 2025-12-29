import flet as ft
from gui.app import main as gui_main
import traceback

def main():
    try:    
        ft.app(target=gui_main)
    except Exception:
        error_path = "crash_log.txt"
        with open(error_path, "w") as f:
            f.write(traceback.format_exc())

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    main()
