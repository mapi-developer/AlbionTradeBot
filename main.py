from net.sniffer import AlbionSniffer
import sys

def main():
    # Check for admin/root privileges (needed for sniffing)
    try:
        sniffer = AlbionSniffer()
        sniffer.start()
    except PermissionError:
        print("Error: Packet sniffing requires Administrator/Root privileges.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nStopping Sniffer...")

if __name__ == "__main__":
    main()