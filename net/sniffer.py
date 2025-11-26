from scapy.all import sniff, UDP
from .photon_layer import PhotonLayerDecoder
from photon.decoder import PhotonDataDecoder
import photon.constants as const
import json
import struct
import io
from datetime import datetime

OP_AUCTION_GET_ITEM_AVERAGE_STATS = 123

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
        
        # CACHE: Maps MessageID -> {item_id, quality, timescale}
        self.history_request_cache = {}

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
        msg_type = ord(stream.read(1))

        # -------------------------------------------------------
        # 1. HANDLE REQUESTS (Client -> Server)
        # We capture the request to know WHICH item is being asked for
        # -------------------------------------------------------
        if msg_type == 2: # Operation Request
            op_code = ord(stream.read(1))
            
            if op_code == OP_AUCTION_GET_ITEM_AVERAGE_STATS:
                params = PhotonDataDecoder(stream).decode()
                
                # Mapstructure from Go file:
                # 1: ItemID (int), 2: Quality, 3: Timescale, 255: MessageID
                msg_id = params.get(255)
                item_id = params.get(1)
                quality = params.get(2)
                timescale = params.get(3)
                
                if msg_id and item_id:
                    # Store in cache
                    self.history_request_cache[msg_id] = {
                        "item_id": item_id,
                        "quality": quality,
                        "timescale": timescale,
                        "timestamp": datetime.utcnow()
                    }
                    # Clean old cache occasionally (omitted for brevity)

        # -------------------------------------------------------
        # 2. HANDLE RESPONSES (Server -> Client)
        # -------------------------------------------------------
        elif msg_type in [3, 7]: 
            op_code = ord(stream.read(1))
            stream.read(2) # Return Code
            
            # Skip Debug String
            debug_type = ord(stream.read(1))
            if debug_type == 115: 
                length = struct.unpack(">H", stream.read(2))[0]
                stream.read(length)
            
            # Decode Data
            params = PhotonDataDecoder(stream).decode()
            
            # Check if this is a History Response
            # It usually contains arrays at keys 0 (item_amt), 1 (silver), 2 (time)
            # And crucially, key 255 (MessageID) to match our request
            msg_id = params.get(255)
            
            if msg_id in self.history_request_cache:
                # MATCH FOUND!
                req_info = self.history_request_cache.pop(msg_id) # Retrieve and remove
                self.handle_history_response(req_info, params)
                
            # Existing Market Order Logic
            elif 0 in params and isinstance(params[0], (str, list)): 
                self.handle_market_data(params[0])

    def handle_market_data(self, data_obj):
        if isinstance(data_obj, str):
            self.parse_json(data_obj)
        elif isinstance(data_obj, list):
            for s in data_obj:
                if isinstance(s, str):
                    self.parse_json(s)

    def handle_history_response(self, req_info, params):
        """
        Processes the arrays of history data.
        Ref: operation_auction_get_item_average_stats.go
        """
        item_amounts = params.get(0, [])
        silver_amounts = params.get(1, [])
        timestamps = params.get(2, []) # Epoch timestamps
        
        history_rows = []
        
        # Go code logic: handle negative item amounts (offset 256)
        for i in range(len(item_amounts)):
            amt = item_amounts[i]
            if amt < 0:
                amt += 256
            
            row = {
                'item_id': str(req_info['item_id']), # Ensure string
                'location_id': 0, # History is often global or requires location context from state
                'quality': req_info['quality'],
                'timestamp': timestamps[i],
                'item_amount': amt,
                'silver_amount': silver_amounts[i],
                'aggregation_type': str(req_info['timescale']) # 0=24h, 1=7d, 2=4w
            }
            history_rows.append(row)

        if self.db and history_rows:
            print(f"[HISTORY] Captured {len(history_rows)} data points for Item {req_info['item_id']}")
            self.db.add_history(history_rows)

    def parse_json(self, json_str):
        try:
            data = json.loads(json_str)
            if "ItemTypeId" in data and "UnitPriceSilver" in data:
                print(f"[MARKET] {data['ItemTypeId']} | {data['UnitPriceSilver']} Silver")
                if self.db:
                    # CHANGED: Wrap in tuple ('order', data)
                    self.db.write_queue.put(('order', data)) 
        except json.JSONDecodeError:
            pass

    def start(self, interface=None):
        print("Sniffer Started.")
        sniff(filter="udp port 5056", prn=self.packet_callback, store=0, iface=interface)