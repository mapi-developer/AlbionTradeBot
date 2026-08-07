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
        hkl = user32.GetKeyboardLayout(0)
        lang_id = hkl & 0xFFFF
        primary_lang_id = lang_id & 0xFF
        
        return primary_lang_id == 0x09
    except Exception:
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

        # Use ft.run to satisfy Flet >=0.80.0 without deprecation warnings
        ft.run(main=gui_main, assets_dir=assets_path)

        # Force terminate all background daemon threads (Sniffer/Overlay) when Flet exits
        os._exit(0)

    except Exception:
        error_path = "crash_log.txt"
        with open(error_path, "w") as f:
            f.write(traceback.format_exc())
        
        os._exit(1)

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    main()