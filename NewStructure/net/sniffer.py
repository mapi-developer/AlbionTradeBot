from scapy.all import get_if_list, get_if_addr, conf, sniff, UDP, Packet
import io
import socket
import threading
from .photon_command import PhotonLayer
from .reliable_message import ReliableMessage, EventDataType, OperationRequest, OperationResponse
from .fragment_buffer import FragmentBuffer
from .enums import CommandType, MessageType
from . import constants as const

def get_default_interface():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return [i for i in get_if_list() if get_if_addr(i) == s.getsockname()[0]][0]
    except:
        return conf.iface


class Sniffer:
    def __init__(self):
        self.lock = threading.Lock()
        self.frag_buffer = FragmentBuffer()

        self.on_silver_changed = None
        self.on_local_position_changed = None
        self.on_location_changed = None
        self.on_local_player_changed = None
        self.on_equipment_changed = None

        self.request_market_buffer = []
        self.offer_market_buffer = []

        self.running = False

    def start(self):
        iface = get_default_interface()
        self.running = True
        try:
            sniff(
                filter="udp portrange 5055-5056",
                iface=iface,
                prn=self.packet_callback,
                store=0,
                stop_filter=lambda x: not self.running
            )
        except Exception as e:
            print(f"[Sniffer] Exception while sniffing: {e}")

    def stop(self):
        self.running = False

    def packet_callback(self, packet: Packet):
        if not self.running: return
        if not packet.haslayer(UDP): return
        try:
            payload = bytes(packet[UDP].payload)
            layer = PhotonLayer.unpack(io.BytesIO(payload))
            
            for cmd in layer.commands:
                if cmd.type == CommandType.SendReliableType:
                    self.process(cmd.data)
                    
                elif cmd.type == CommandType.SendReliableFragmentType:
                    try:
                        frag = cmd.reliable_fragment()
                        reassembled_cmd = self.frag_buffer.offer(frag)
                        if reassembled_cmd:
                            self.process(reassembled_cmd.data)
                    except Exception as e:
                        print(f"[Sniffer] Fragment Error: {e}")
        except Exception:
            pass

    def process(self, payload):
        pass