from bot import AlbionSniffer

if __name__ == "__main__":
    sniffer = AlbionSniffer()
    try:
        sniffer.start()
    except KeyboardInterrupt:
        sniffer.stop()