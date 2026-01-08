from bot import AlbionSniffer
import threading
import time

def wait_for_user_input():
    try:
        while True:
            time.sleep(.5)
    except KeyboardInterrupt:
        return

if __name__ == "__main__":
    sniffer = AlbionSniffer()
    sniffer_thread = threading.Thread(target=sniffer.start, daemon=True)
    sniffer_thread.start()
    
    wait_for_user_input()
    print(sniffer.get_market_buffer('offer'))
    
    print("Stopping sniffer...")
    sniffer.stop()
    print("Done.")