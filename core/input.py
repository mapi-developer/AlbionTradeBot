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
