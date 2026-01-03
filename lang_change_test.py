import win32api
import win32con
import win32gui  # Required to get the window handle

# Language codes (HKL - Handle to Keyboard Layout)
# Format: Device Handle (High Word) + Language ID (Low Word)
ENGLISH_US = 0x04090409
GERMAN_GERMANY = 0x04070407

def change_keyboard_layout(language_id_hex):
    """
    Switches the active keyboard layout for the currently focused window.
    Note: The layout must already be installed in Windows Settings.
    """
    # Get the handle of the window the user is currently looking at
    hwnd = win32gui.GetForegroundWindow()
    
    if hwnd:
        # WM_INPUTLANGCHANGEREQUEST parameters:
        # wParam: 0 (or INPUTLANGCHANGE_SYSCHARSET)
        # lParam: The language ID handle
        # We use PostMessage because it is non-blocking and safer for cross-process input changes
        win32api.PostMessage(
            hwnd,
            win32con.WM_INPUTLANGCHANGEREQUEST,
            0,
            language_id_hex
        )
        print(f"Request sent to switch layout to: {hex(language_id_hex)}")
    else:
        print("No active window found.")

if __name__ == "__main__":
    change_keyboard_layout(ENGLISH_US)