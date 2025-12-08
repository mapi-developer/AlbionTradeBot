import flet as ft
from gui.app import main as gui_main

def main():
    try:
        ft.app(target=gui_main)
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main()