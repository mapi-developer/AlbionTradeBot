import pyperclip
import pyautogui
import ctypes
import time

class BotStopped(Exception):
    pass


class InputSender():
    def __init__(self):
        self._should_stop_callback = None

    def set_stop_callback(self, callback):
        self._should_stop_callback = callback

    def _check_stop(self):
        if self._should_stop_callback and self._should_stop_callback():
            raise BotStopped("Bot execution stopped by user.")

    def _send_ctrl_v(self):
        """
        Forces a Ctrl+V press using raw Windows Virtual Key codes.
        0x11 = VK_CONTROL
        0x56 = VK_V
        This works even if the active layout is Russian.
        """
        user32 = ctypes.windll.user32
        
        # Press Ctrl (0x11)
        user32.keybd_event(0x11, 0, 0, 0)
        # Press V (0x56)
        user32.keybd_event(0x56, 0, 0, 0)
        
        # Release V
        user32.keybd_event(0x56, 0, 2, 0) # 2 = KEYEVENTF_KEYUP
        # Release Ctrl
        user32.keybd_event(0x11, 0, 2, 0)

    def sleep(self, seconds: int) -> None:
        end_time = time.time() + seconds
        while time.time() < end_time:
            self._check_stop()
            sleep_time = min(0.1, end_time - time.time())
            time.sleep(sleep_time)

    def typewrite(self, text: str | int) -> None:
        self._check_stop()
        if type(text) == str:
            text = text if len(text) >= 10 else text + "          "
        else:
            text = str(text)
        pyautogui.typewrite(text, 0.03)
        # pyperclip.copy(text)
        # self.sleep(0.05)
        # self._send_ctrl_v()
        # self.sleep(.1)

    def press(self, keycode: str) -> None:
        self._check_stop()
        pyautogui.press(keycode)

    def click(self, position: list[int], clicks: int = 1, interval: float = 0.02) -> None:
        self._check_stop()
        pyautogui.click(position, clicks=clicks, interval=interval)

    def right_click(self, position: list[int]) -> None:
        self._check_stop()
        pyautogui.rightClick(position)

    def click_with_key(self, position: list[int], key: str, clicks: int = 1) -> None:
        self._check_stop()
        with pyautogui.hold(key):
            self.click(position, clicks=clicks)
            self.sleep(.1)

    def right_click_with_key(self, position: list[int], key: str) -> None:
        self._check_stop()
        with pyautogui.hold(key):
            self.right_click(position)
            self.sleep(.1)

    def drag(self, start_pos: list[int], end_pos: list[int], duration: float = 0.5) -> None:
        self._check_stop()
        pyautogui.moveTo(start_pos[0], start_pos[1])
        pyautogui.mouseDown(button='left')
        pyautogui.moveTo(end_pos[0], end_pos[1], duration=duration)
        pyautogui.mouseUp(button='left')

    def scroll(self, clicks: int = 15) -> None:
        self._check_stop()
        pyautogui.scroll(clicks)

    def key_down(self, key: str) -> None:
        self._check_stop()
        pyautogui.keyDown(key)

    def key_up(self, key: str) -> None:
        pyautogui.keyUp(key)