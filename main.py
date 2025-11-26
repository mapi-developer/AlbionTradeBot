# main.py
from net.sniffer import AlbionSniffer
from scapy.all import dev_from_index, show_interfaces
import sys

# !!! IMPORTANT !!!
# Run this once, find the INDEX of your Ethernet/Wi-Fi, and set it here.
TARGET_INDEX = 14

def main():
    print("--- Network Interfaces ---")
    show_interfaces()
    print("--------------------------")
    
    try:
        my_iface = dev_from_index(TARGET_INDEX)
    except Exception:
        print(f"Error: Interface Index {TARGET_INDEX} not found.")
        return

    print(f"Launching Sniffer on: {my_iface}")
    sniffer = AlbionSniffer()
    
    try:
        sniffer.start(interface=my_iface)
    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    main()