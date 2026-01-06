from ..core import WindowCapture, InputSender
from ..managers import SettingsManager

class LoginManager(InputSender):
    def __init__(self, bot, capture: WindowCapture = None, settings: SettingsManager = None):
        super().__init__()
        if capture == None: capture = WindowCapture("Albion Online Client")
        if settings == None: settings = SettingsManager()

        self.bot = bot
        self.capture = capture
        self.settings = settings
        self.capture_positions = self.settings.CAPTURE_POSITIONS[capture.get_window_resolution()]["login"]
        self.mouse_positions = self.settings.MOUSE_POSITIONS[capture.get_window_resolution()]["login"]

    def check_login(self):
        self.capture.set_foreground_window()
        if self.capture.get_text_from_screenshot(self.capture_positions["login_title"]) != "login":
            return
        while self.capture.get_text_from_screenshot(self.capture_positions["server_notice"]) == "server notice":
            print("Sevrer Restart")
            self.sleep(30)
            self.bot._wait_if_paused()
        
        self.click(self.mouse_positions["button_login"])
        while self.capture.get_text_from_screenshot(self.capture_positions["characters_title"]) != "characters":
            self.sleep(.5)
            self.bot._wait_if_paused()
            if self.capture.get_text_from_screenshot(self.capture_positions["try_again"]).find("again"):
                self.click(self.mouse_positions["button_try_again_ok"])
                self.sleep(.3)
                self.click(self.mouse_positions["button_login"])

        self.click(self.mouse_positions["button_enter_world"])
        self.sleep(5)
        self.press("esc")
        if self.capture.get_text_from_screenshot(self.capture_positions["activities"]) == "activities":
            self.click(self.mouse_positions["button_close_activities"])

    def logout(self):
        if self.bot.current_location in self.settings.MARKETS:
            self.press("esc")
        self.press("esc")
        self.click(self.mouse_positions["button_logout"])
        self.sleep(14)
        
    def login_into_account(self, email: str, password: str):
        self.click(self.mouse_positions["button_email"])
        self.typewrite(email)
        self.click(self.mouse_positions["button_password"])
        self.typewrite(password)

    def change_account(self, email: str, password: str):
        self.logout()
        self.login_into_account(email=email, password=password)