import flet as ft
from gui.gui import main as gui_main

def main():
    """
    Launches the Flet GUI application.
    """
    try:
        # The gui_main function from gui.py expects a 'page' object.
        # ft.app will provide this when it calls the target function.
        ft.app(target=gui_main)
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main()