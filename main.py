from net.sniffer import AlbionSniffer
from scapy.all import dev_from_index, show_interfaces
import sys

# SET YOUR INTERFACE INDEX HERE
# Run this script once to see the list, then change this number.
TARGET_INDEX = 14

def main():
    # 1. Print available interfaces so you can confirm the index
    print("Available Interfaces:")
    show_interfaces()
    print("-" * 30)

    try:
        # 2. Resolve the index to the actual interface object
        # dev_from_index handles the conversion from '1' to '\Device\NPF_...'
        my_iface = dev_from_index(TARGET_INDEX)
    except Exception:
        print(f"Error: Could not find interface with index {TARGET_INDEX}")
        print("Please check the list above and update TARGET_INDEX in main.py")
        return

    # 3. Start Sniffer
    sniffer = AlbionSniffer()
    try:
        sniffer.start(interface=my_iface)
    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()