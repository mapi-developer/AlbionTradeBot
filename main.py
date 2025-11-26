from net.sniffer import AlbionSniffer
from database.interface import DatabaseInterface # Import DB
from scapy.all import dev_from_index, show_interfaces
import sys

TARGET_INDEX = 14

def main():
    print("--- Network Interfaces ---")
    show_interfaces()
    
    # 1. Initialize Database
    try:
        db = DatabaseInterface()
        print("Database connection established.")
    except Exception as e:
        print(f"Database connection failed: {e}")
        return

    # 2. Find Interface
    try:
        my_iface = dev_from_index(TARGET_INDEX)
    except Exception:
        print(f"Error: Interface Index {TARGET_INDEX} not found.")
        return

    # 3. Start Sniffer (Pass DB instance)
    print(f"Launching Sniffer on: {my_iface}")
    sniffer = AlbionSniffer(db_interface=db) # <--- Pass DB here
    
    try:
        sniffer.start(interface=my_iface)
    except KeyboardInterrupt:
        db.running = False # Stop DB worker
        print("\nStopped.")

if __name__ == "__main__":
    main()