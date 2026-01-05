import flet as ft
from gui.app import main as gui_main
import traceback
import sys, os

def get_asset_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def main():
    try:    
        ft.app(target=gui_main, assets_dir="assets")
    except Exception:
        error_path = "crash_log.txt"
        with open(error_path, "w") as f:
            f.write(traceback.format_exc())

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    main()