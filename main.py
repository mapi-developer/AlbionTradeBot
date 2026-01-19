import flet as ft
from gui.app import main as gui_main
import traceback
import sys
import os
import ctypes

def is_english_layout():
    """
    Checks if the current keyboard layout is English.
    English Language Identifier is 0x09.
    """
    try:
        user32 = ctypes.windll.user32
        # GetKeyboardLayout(0) retrieves the layout for the current thread
        hkl = user32.GetKeyboardLayout(0)
        # The Language ID is the lower 16 bits
        lang_id = hkl & 0xFFFF
        # The Primary Language ID is the lower 8 bits (0x09 is English)
        primary_lang_id = lang_id & 0xFF
        
        return primary_lang_id == 0x09
    except Exception:
        # If we fail to check, we assume True to avoid blocking the user erroneously
        return True

def get_asset_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

def main():
    if not is_english_layout():
        ctypes.windll.user32.MessageBoxW(
            0, 
            "Please restart app with English keyboard layout", 
            "Keyboard Layout Error", 
            0x10 | 0x00
        )
        sys.exit(0)
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