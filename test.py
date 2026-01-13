import pyautogui
from bot import Bot
import time
from pynput import mouse
from bot import KeyboardTravelManager

run = True
def wait_for_user_input():
    global run
    try:
        while True:
            time.sleep(.5)
    except KeyboardInterrupt:
        run = False
        return
    
def on_click(x, y, button, pressed):
    # Only print when the button is pressed (not released)
    if pressed:
        print(f"Mouse clicked at position: ({x}, {y}) with {button}")
        
        # Optional: Stop listener if the right mouse button is clicked
        if button == mouse.Button.left:
            return False

    # Set up the listener


if __name__ == "__main__":
    bot = Bot()
    manager = KeyboardTravelManager(bot)
    wait_for_user_input()
    print()
    bot.capture.set_foreground_window()
    #print(bot.sniffer.current_position)
    #print(bot.sniffer.travel_planner_point)
    #planner_pos = [218.0, -208.0]
    #pos = bot.travel_manager.calculate_click_position(bot.sniffer.current_position, bot.sniffer.travel_planner_point, 400)
    #bot.travel_manager.click(pos)
    #pyautogui.moveTo(pos)
    # with mouse.Listener(on_click=on_click) as listener:
    #     listener.join()
    # wait_for_user_input()
    manager.move_to_position([223.0984, -191.6673])
    print()
    
    bot.destroy()
    print("Done.")