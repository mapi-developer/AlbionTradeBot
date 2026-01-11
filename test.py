from bot import Bot
import threading
import time
run = True
def wait_for_user_input():
    global run
    try:
        while True:
            time.sleep(.5)
    except KeyboardInterrupt:
        run = False
        return

if __name__ == "__main__":
    bot = Bot()
    time.sleep(3)
    while run:
        time.sleep(.5)
        bot.travel_manager.move_step([221, -207])
    
    wait_for_user_input()
    bot.destroy()
    print("Done.")