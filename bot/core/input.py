import pyautogui
import time

class InputSender():
    def sleep(self, seconds: int) -> None:
        time.sleep(seconds)

    def typewrite(self, text: str | int) -> None:
        if type(text) == str:
            text = text if len(text) >= 10 else text + "          "
        else:
            text = str(text)
        pyautogui.typewrite(text, 0.03)

    def press(self, keycode: str) -> None:
        pyautogui.press(keycode)

    def click(self, position: list[int], clicks: int = 1, interval: float = 0.02) -> None:
        pyautogui.click(position, clicks=clicks, interval=interval)

    def right_click(self, position: list[int]) -> None:
        pyautogui.rightClick(position)

    def click_with_key(self, position: list[int], key: str, clicks: int = 1) -> None:
        """
        Holds down a key (shift, ctrl, alt), performs a click, then releases the key.
        """
        with pyautogui.hold(key):
            self.click(position, clicks=clicks)
            self.sleep(.1)

    def right_click_with_key(self, position: list[int], key: str) -> None:
        """
        Holds down a key (shift, ctrl, alt), performs a click, then releases the key.
        """
        with pyautogui.hold(key):
            self.right_click(position)
            self.sleep(.1)

    def drag(self, start_pos: list[int], end_pos: list[int], duration: float = 0.5) -> None:
        """
        Moves to start_pos, holds left click, moves to end_pos, and releases.
        """
        pyautogui.moveTo(start_pos[0], start_pos[1])
        pyautogui.mouseDown(button='left')
        pyautogui.moveTo(end_pos[0], end_pos[1], duration=duration)
        pyautogui.mouseUp(button='left')

    def scroll(self, clicks: int = 15) -> None:
        pyautogui.scroll(clicks)

    def key_down(self, key: str) -> None:
        """Holds a key down."""
        # print(f"[Input] Key Down: {key}")
        pyautogui.keyDown(key)

    def key_up(self, key: str) -> None:
        """Releases a key."""
        # print(f"[Input] Key Up: {key}")
        pyautogui.keyUp(key)