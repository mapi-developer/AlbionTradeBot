import flet as ft
from gui.app import main as gui_main
import traceback
import sys
import os
import ctypes

def get_asset_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

def main():
    try:
        myappid = 'mapideveloper.albiontradebot.markettrader.1.0'
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

        assets_path = get_asset_path("config")
        
        if not os.path.exists(assets_path):
            with open("asset_error.txt", "w") as f:
                f.write(f"Could not find assets at: {assets_path}")

        ft.app(target=gui_main, assets_dir=assets_path)

    except Exception:
        error_path = "crash_log.txt"
        with open(error_path, "w") as f:
            f.write(traceback.format_exc())

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    main()