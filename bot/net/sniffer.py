import socket
from scapy.all import get_if_list, get_if_addr, conf, sniff, UDP
import struct
import io
import gzip
import json
import threading
from datetime import datetime, timezone

# Import your local modules
from . import constants as const
from .layer import PhotonLayerDecoder
from .decoder import PhotonDataDecoder

# --- Fragment Handling ---
class FragmentBuffer:
    def __init__(self):
        self.buffers = {} 
    def handle(self, payload):
        if len(payload) < 20: return None
        seq_id, frag_count, frag_num, total_len, offset = struct.unpack(">iiiii", payload[:20])
        data = payload[20:]
        if seq_id not in self.buffers: self.buffers[seq_id] = {"count": frag_count, "parts": {}}
        self.buffers[seq_id]["parts"][frag_num] = data
        if len(self.buffers[seq_id]["parts"]) == frag_count:
            parts = self.buffers.pop(seq_id)["parts"]
            return b"".join([parts[i] for i in range(frag_count)])
        return None

def get_default_interface():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return [i for i in get_if_list() if get_if_addr(i) == s.getsockname()[0]][0]
    except: return conf.iface

class AlbionSniffer:
    def __init__(self):
        self.layer_decoder = PhotonLayerDecoder()
        self.frag_buffer = FragmentBuffer()
        self.running = False
        
        # --- BUFFERS ---
        self.current_silver = 0
        self.market_buffer = []
        self.offer_market_buffer = []
        self.request_market_buffer = []
        self.mail_buffer = []
        self.lock = threading.Lock()

    def start(self):
        iface = get_default_interface()
        print(f">>> Sniffer Started on Interface: {iface}")
        self.running = True
        
        # MODIFIED: Loop with timeout to allow stopping
        while self.running:
            # timeout=1 yields control back every 1 second so we can check self.running
            sniff(
                filter="udp port 5056", 
                iface=iface, 
                prn=self.packet_callback, 
                store=0,
                timeout=1  # <--- CRITICAL ADDITION
            )
        print(">>> Sniffer Stopped")

    def stop(self):
        """Signal the sniffer loop to stop."""
        self.running = False

    def packet_callback(self, packet):
        if not self.running: return # Extra safety check
        if not packet.haslayer(UDP): return
        try:
            for cmd in self.layer_decoder.decode_packet(bytes(packet[UDP].payload)):
                if cmd.type == const.COMMAND_SEND_RELIABLE: self.process(cmd.payload)
                elif cmd.type == const.COMMAND_SEND_FRAGMENT:
                    msg = self.frag_buffer.handle(cmd.payload)
                    if msg: self.process(msg)
        except: pass

    def process(self, payload):
        if payload[:2] == b'\x1f\x8b': 
            try: payload = gzip.decompress(payload)
            except: return
        
        stream = io.BytesIO(payload)
        try:
            stream.read(1)
            msg_type = ord(stream.read(1))
            op = 0

            if msg_type == 2: op = ord(stream.read(1))
            elif msg_type == 3: op = ord(stream.read(1)); stream.read(3)
            elif msg_type == 4: op = ord(stream.read(1))
            else: return

            params = PhotonDataDecoder(stream).decode()

            # --- MAIL CONTENT (OpCode 1) ---
            if op == const.OP_GET_MAIL_INFOS and 1 in params:
                self.handle_read_mail(params)
                
            if msg_type == 4:
                event_code = params.get(252)
                if event_code == const.OP_EVENT_UPDATE_SILVER:
                    self.handle_silver_update(params)

            # --- MARKET DATA ---
            self.scan_for_market_data(params)
        except Exception as e:
            print(f"Sniffer Error: {e}")

    def handle_silver_update(self, params):
        silver = params.get(1)
        if silver is not None:
            try:
                silver_val = int(silver) 
                
                with self.lock:
                    self.current_silver = int(f"{silver_val/10000:.0f}")
                print(f">>> Updated Silver: {self.current_silver}") 
            except Exception as e:
                print(f"Error parsing silver: {e}")

    def handle_read_mail(self, params):
        mail_id = params.get(0)
        content_raw = params.get(1)
        
        if mail_id and content_raw:
            try:
                if isinstance(content_raw, (bytes, bytearray, list)):
                    if isinstance(content_raw, list): content_raw = bytes(content_raw)
                    content_str = content_raw.decode('utf-8', errors='ignore')
                else:
                    content_str = str(content_raw)
                
                content_str = content_str.replace('\x00', '')
                
                if '|' in content_str:
                    self.parse_smart_mail(mail_id, content_str)
            except: pass

    def parse_smart_mail(self, mail_id, content):
        parts = content.split('|')
        if len(parts) < 4: return

        def is_item_name(s):
            return (len(s) > 2 and not s.replace('.', '').isdigit())

        data = {
            'mail_id': mail_id,
            'timestamp': datetime.now(timezone.utc)
        }

        # CHECK 1: FINISHED ORDER
        if is_item_name(parts[1]) and parts[0].replace('.', '').isdigit():
            try:
                data['transaction_type'] = "MARKETPLACE_FINISHED"
                data['amount'] = int(float(parts[0]))
                data['item_unique_name'] = parts[1]
                data['total_silver'] = int(float(parts[2])) // 10000
                data['unit_price'] = int(float(parts[3])) // 10000
                
                with self.lock:
                    self.mail_buffer.append(data)
                return
            except: pass

        # CHECK 2: EXPIRED ORDER
        if is_item_name(parts[3]) and parts[1].replace('.', '').isdigit():
            try:
                data['transaction_type'] = "MARKETPLACE_EXPIRED"
                data['amount'] = int(float(parts[1]))
                data['item_unique_name'] = parts[3]
                data['total_silver'] = int(float(parts[2])) // 10000
                data['unit_price'] = 0
                
                with self.lock:
                    self.mail_buffer.append(data)
                return
            except: pass

    def scan_for_market_data(self, data):
        if isinstance(data, dict):
            if "ItemTypeId" in data and "UnitPriceSilver" in data:
                self._handle_market_order(data)
            else:
                for v in data.values():
                    self.scan_for_market_data(v)
        elif isinstance(data, list):
            for item in data:
                self.scan_for_market_data(item)
        elif isinstance(data, str):
            if data.startswith('{') or data.startswith('['):
                try:
                    parsed = json.loads(data)
                    self.scan_for_market_data(parsed)
                except: pass

    def _handle_market_order(self, order):
        try:
            with self.lock:
                if order.get("AuctionType") == "offer":
                    self.offer_market_buffer.append(order)
                elif order.get("AuctionType") == "request":
                    self.request_market_buffer.append(order)
        except Exception:
            pass

    # --- EXTERNAL METHODS (For Bot Instance) ---

    def get_market_buffer(self, type: str = None):
        
        with self.lock:
            offer_data = list(self.offer_market_buffer)
            request_data = list(self.request_market_buffer)
            self.offer_market_buffer.clear()
            self.request_market_buffer.clear()
            if type == "offer":
                return offer_data
            elif type == "request":
                return request_data
            else:
                return offer_data, request_data

    def get_mail_buffer(self):
        """Returns the list of buffered mails and clears the buffer."""
        with self.lock:
            data = list(self.mail_buffer)
            self.mail_buffer.clear()
            return data

if __name__ == "__main__":
    sniffer = AlbionSniffer()
    try:
        sniffer.start()
    except KeyboardInterrupt:
        sniffer.stop()