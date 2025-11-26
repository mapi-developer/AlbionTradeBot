from scapy.all import sniff, UDP
from .photon_layer import PhotonLayerDecoder
from photon.decoder import PhotonDataDecoder
import photon.constants as const
import json
import struct
import io

class FragmentBuffer:
    def __init__(self):
        self.buffers = {}

    def handle_fragment(self, payload):
        if len(payload) < 20: return None
        seq_id, frag_count, frag_num, total_len, offset = struct.unpack(">iiiii", payload[:20])
        data = payload[20:]

        if seq_id not in self.buffers:
            self.buffers[seq_id] = {"count": frag_count, "parts": {}}
        
        self.buffers[seq_id]["parts"][frag_num] = data

        if len(self.buffers[seq_id]["parts"]) == frag_count:
            parts = self.buffers.pop(seq_id)["parts"]
            return b"".join([parts[i] for i in range(frag_count)])
        return None

class AlbionSniffer:
    def __init__(self, db_interface=None):
        self.layer_decoder = PhotonLayerDecoder()
        self.frag_buffer = FragmentBuffer()
        self.db = db_interface

    def packet_callback(self, packet):
        if not packet.haslayer(UDP): return
        if packet[UDP].sport != 5056 and packet[UDP].dport != 5056: return

        try:
            payload = bytes(packet[UDP].payload)
            commands = self.layer_decoder.decode_packet(payload)

            for cmd in commands:
                if cmd.type == const.COMMAND_SEND_RELIABLE:
                    self.process_reliable(cmd.payload)
                elif cmd.type == const.COMMAND_SEND_FRAGMENT:
                    full_msg = self.frag_buffer.handle_fragment(cmd.payload)
                    if full_msg: self.process_reliable(full_msg)
        except Exception:
            pass

    def process_reliable(self, payload):
        stream = io.BytesIO(payload)
        stream.read(1) # Signature
        msg_type = ord(stream.read(1)) # Type

        if msg_type in [3, 7]: # Operation Response
            op_code = ord(stream.read(1))
            stream.read(2) # Return Code
            
            # Debug String
            debug_type = ord(stream.read(1))
            if debug_type == 115: # String
                length = struct.unpack(">H", stream.read(2))[0]
                stream.read(length)
            
            # Dictionary
            params = PhotonDataDecoder(stream).decode()
            if 0 in params:
                self.handle_market_data(params[0])

    def handle_market_data(self, data_obj):
        if isinstance(data_obj, str):
            self.parse_json(data_obj)
        elif isinstance(data_obj, list):
            for s in data_obj:
                if isinstance(s, str):
                    self.parse_json(s)

    def parse_json(self, json_str):
        try:
            data = json.loads(json_str)
            print(data)
            if "ItemTypeId" in data and "UnitPriceSilver" in data:
                print(f"[MARKET] {data['ItemTypeId']} | {data['UnitPriceSilver']} Silver")
                if self.db:
                    self.db.add_order(data)
        except json.JSONDecodeError:
            pass

    def start(self, interface=None):
        print("Sniffer Started.")
        sniff(filter="udp port 5056", prn=self.packet_callback, store=0, iface=interface)