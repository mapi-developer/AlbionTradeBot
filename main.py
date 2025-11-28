from net.sniffer import AlbionSniffer
from database.interface import DatabaseInterface
from scapy.all import dev_from_index, show_interfaces
from core.capture import WindowCapture
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_INDEX = 14

def main():
    print("--- Network Interfaces ---")
    show_interfaces()
    
    # 1. Start Database
    try:
        db = DatabaseInterface()
        print("Database connection established.")
    except Exception as e:
        print(f"Error connecting to DB: {e}")
        print("Make sure Docker is running: docker-compose up -d")
        return

    # 2. Select Interface
    try:
        my_iface = dev_from_index(TARGET_INDEX)
    except Exception:
        print(f"Error: Interface {TARGET_INDEX} not found.")
        return

    # 3. Run Sniffer
    sniffer = AlbionSniffer(db_interface=db)
    try:
        sniffer.start(interface=my_iface)
    except KeyboardInterrupt:
        db.running = False
        print("\nStopping...")

def test():
    cap = WindowCapture(base_dir=BASE_DIR, window_name="Albion Online Client", debugging=False)
    print(cap.get_text_from_screenshot([]))

if __name__ == "__main__":
    test()