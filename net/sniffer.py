from scapy.all import sniff, UDP
from .photon_layer import PhotonLayerDecoder
from photon.decoder import PhotonDataDecoder
import photon.constants as const
from utils.items import ItemManager
import json
import struct
import io
import gzip

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
        self.items = ItemManager()
        self.history_cache = {}
        self.market_data_buffer = []

    def clear_buffer(self):
        self.market_data_buffer = []

    def start(self, interface=None):
        print(">>> Sniffer Started. Listening for Market Data...")
        sniff(filter="udp port 5056", prn=self.packet_callback, store=0, iface=interface)

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
        # GZIP Decompression
        if len(payload) > 2 and payload[:2] == b'\x1f\x8b':
            try:
                payload = gzip.decompress(payload)
            except:
                return

        stream = io.BytesIO(payload)
        stream.read(1) 
        msg_type = ord(stream.read(1))

        if msg_type == 2: # Request
            self.handle_request(stream)
        elif msg_type in [3, 7]: # Response
            self.handle_response(stream)
        elif msg_type == 4: # Event
            self.handle_event(stream)

    def handle_request(self, stream):
        try:
            op_code = ord(stream.read(1))
            params = PhotonDataDecoder(stream).decode()
            
            # History Request (Key 1=Item, 3=Time)
            if 1 in params and 255 in params:
                msg_id = params[255]
                item_id = params[1]
                if item_id < 0 and item_id > -129: item_id += 256
                db_name = self.items.get_name(item_id)
                self.history_cache[msg_id] = {
                    "item_db_name": db_name,
                    "quality": params.get(2, 0),
                    "timescale": params.get(3, 0)
                }
        except: pass

    def handle_response(self, stream):
        try:
            op_code = ord(stream.read(1))
            stream.read(2)
            debug_type = ord(stream.read(1))
            if debug_type == 115:
                length = struct.unpack(">H", stream.read(2))[0]
                stream.read(length)
            
            params = PhotonDataDecoder(stream).decode()

            # Check History Match
            if msg_id := params.get(255):
                if msg_id in self.history_cache:
                    req = self.history_cache.pop(msg_id)
                    self.parse_history(req, params)
                    return

            # Scan for Market Orders
            self.scan_recursive(params)

        except: pass

    def handle_event(self, stream):
        try:
            event_code = ord(stream.read(1))
            params = PhotonDataDecoder(stream).decode()
            
            # Scan for Market Orders
            self.scan_recursive(params)
        except: pass

    def scan_recursive(self, data):
        """
        Scans for Market Data (JSON strings or Dicts).
        """
        if isinstance(data, dict):
            # Check for Market Order structure
            if "ItemTypeId" in data and "UnitPriceSilver" in data:
                self.process_market_order(data)

            for val in data.values():
                self.scan_recursive(val)

        elif isinstance(data, list):
            for item in data:
                self.scan_recursive(item)

        elif isinstance(data, str):
            # Parse embedded JSON
            if data.strip().startswith("{") or data.strip().startswith("["):
                try:
                    parsed = json.loads(data)
                    self.scan_recursive(parsed)
                except:
                    pass

    def process_market_order(self, data):
        try:
            data['item_db_name'] = data.get('ItemTypeId')
            # print(f"   >>> [MARKET] Found: {data['item_db_name']} | {data.get('UnitPriceSilver')} Silver")
            self.market_data_buffer.append(data)
            if self.db: self.db.add_order(data)
        except: pass

    def parse_history(self, req, params):
        try:
            if 0 not in params or 1 not in params: return
            item_amts = params[0]
            silver_amts = params[1]
            timestamps = params[2]
            
            # Ensure timestamps is a list to prevent crashes
            if not isinstance(timestamps, list): return

            history_list = []
            for i in range(len(timestamps)):
                amt = item_amts[i]
                if amt < 0: amt += 256
                
                history_list.append({
                    "item_db_name": req['item_db_name'],
                    "quality": req['quality'],
                    "location_id": 3005, 
                    "timestamp": timestamps[i],
                    "aggregation_type": req['timescale'],
                    "item_amount": amt,
                    "silver_amount": silver_amts[i]
                })
            
            if self.db:
                # print(f"   >>> [HISTORY] Captured {len(history_list)} records for {req['item_db_name']}")
                self.db.add_history(history_list)
        except: pass