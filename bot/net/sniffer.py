import gzip
import io
import struct
import socket
import threading
import json
from datetime import datetime, timezone
from scapy.all import get_if_list, get_if_addr, conf, sniff, UDP
import math

from . import constants as const
from .layer import PhotonLayerDecoder
# from .decoder import PhotonDataDecoder  <-- Removed, replaced by message.py
from .fragment import FragmentBuffer, ReliableFragment
from .message import ReliableMessage, MessageType
from .graph import WaypointGraph

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
        self.lock = threading.Lock()

        self.graph = WaypointGraph()
        self.node_counter = 0
        self.local_player_id = ""
        self.character_name = ""

        self.current_silver = 0
        self.characters = {}
        self.inventory = {}
        self.equipment = {}

        self.current_position = None
        self.current_speed = 0.0
        self.last_recorded_pos = None

        self.offer_market_buffer = []
        self.request_market_buffer = []
        self.mail_buffer = []
        
    def start(self):
        iface = get_default_interface()
        print(f"[Sniffer] >>> Started on Interface: {iface}")
        self.running = True

        try:
            sniff(
                filter="udp portrange 5050-5100",
                iface=iface,
                prn=self.packet_callback,
                store=0,
                stop_filter=lambda x: not self.running
            )
        except Exception as e:
            print(f"[Sniffer] Error: {e}")

    def stop(self):
        self.running = False

    def get_current_position(self):
        return list(self.current_position)

    def packet_callback(self, packet):
        if not self.running: return
        if not packet.haslayer(UDP): return

        try:
            for cmd in self.layer_decoder.decode_packet(bytes(packet[UDP].payload)):
                if cmd.type == const.COMMAND_SEND_RELIABLE:
                    self.process(cmd.payload)
                elif cmd.type == const.COMMAND_SEND_FRAGMENT:
                    try:
                        stream = io.BytesIO(cmd.payload)
                        frag = ReliableFragment.unpack(stream)
                        if frag:
                            reassembled_msg = self.frag_buffer.offer(frag)
                            if reassembled_msg:
                                self.process(reassembled_msg)
                    except Exception as e:
                        print(f"[Sniffer] Fragment Error: {e}")
        except Exception as e:
            print(f"[Sniffer] >>> Packet Callback Exception: {e}")

    def process(self, payload):
        if payload[:2] == b'\x1f\x8b':
            try: payload = gzip.decompress(payload)
            except: return

        try:
            # Use ReliableMessage to unpack the header and parameters safely
            stream = io.BytesIO(payload)
            msg = ReliableMessage.unpack(stream)
            if not msg:
                return

            params = msg.parameters
            op_code = msg.operation_code
            event_code = msg.event_code

            if 253 in params:
                op_code = params[253]
                if op_code == 21:
                    current_pos = params.get(1) # List [x, y]
                    angle = params.get(2)
                    speed = params.get(4)       # Float
                    
                    if current_pos != None:
                        self.current_position = current_pos
                        #print(f"POS: {self.current_position}", flush=True, end="           \r")
                        #self.record_path()
            elif msg.type == MessageType.EventData:
                event_code = params.get(252)
                filter = []
                if event_code not in filter:
                    pass
                    #print(params)
                if not event_code: event_code = op_code
                
                if event_code == const.OP_CHARACTER_EQUIPMENT_CHANGED:
                    self.handle_equipment_changed(params)
                elif event_code == const.EVENT_NEW_ITEM:
                    self.handle_new_item(params)
                elif event_code == const.OP_NEW_CHARACTER:
                    self.handle_new_character(params)
                elif event_code == const.OP_EVENT_UPDATE_SILVER:
                    self.handle_silver_update(params)
                elif event_code == const.EVENT_RESOURCE:
                    #print(params)
                    pass
                
                # Check 252 for sub-event if main event_code is generic
                sub_code = params.get(252)
                if sub_code == 2: # Join Response often hides here in events
                    self.handle_join_response(params)

            # Handle Operation Response (Type 2, 3, 7)
            # Note: Albion often sends Join Response as OpCode 2
            elif msg.type in (MessageType.OperationRequest, MessageType.OperationResponse, MessageType.OtherOperationResponse):
                
                # Fallback for Join Response logic
                if op_code == 2: # Join Request Response
                     self.handle_join_response(params)
                
                # Mail Infos
                elif op_code == const.OP_GET_MAIL_INFOS and 1 in params:
                    self.handle_read_mail(params)

            # Always scan parameters for Market Data (it can be in OpResponse or Events)
            self.scan_for_market_data(params)

        except Exception as e:
            pass
            #print(f"[Sniffer] >>> Processing Exception: {e}")

    # --- Handlers remain largely the same ---

    def record_path(self):
        # This simulates data coming from your Sniffer process() method
        current_pos = self.current_position # You need to implement this getter
        
        if self.last_recorded_pos is None:
            self.graph.add_node(self.node_counter, current_pos)
            self.last_recorded_pos = current_pos
            self.node_counter += 1
            print("node added")
        else:
            dist = math.dist(current_pos, self.last_recorded_pos)
            if dist > 3.0: # Only add a node every 3 meters
                self.graph.add_node(self.node_counter, current_pos)
                # Connect to previous node
                self.graph.add_connection(self.node_counter - 1, self.node_counter)
                self.last_recorded_pos = current_pos
                self.node_counter += 1
                print(f"Recorded Node {self.node_counter}: {current_pos}")

    def handle_join_response(self, params: dict):
        try:
            # Check if this really looks like a join response
            if 0 in params and 2 in params: # ID and Name
                print("join response")
                self.reset_session() 
                self.local_player_id = params[0]
                print(f"[Sniffer] >>> Join Complete! Local Player ID: {self.local_player_id}")
                self.character_name = params[2]
                print(f"[Sniffer] >>> Character Name: {self.character_name}")
        except Exception as e:
            print(f"[Sniffer] >>> Handle Join Error: {e}")

    def handle_equipment_changed(self,  params: dict):
        user_id = params.get(0)
        equipment = params.get(2)
        if equipment and isinstance(equipment, list):
            if user_id in self.characters.keys():
                self.characters[user_id] = equipment
            else:
                self.equipment = equipment

    def handle_new_item(self, params: dict):
        try:
            print("new Item")
            local_item_id = params.get(0)
            item_index = params.get(1)
            if local_item_id is not None and item_index is not None:
                with self.lock:
                    if item_index not in self.equipment:
                        self.inventory[local_item_id] = item_index
        except Exception as e:
            print(f"[Sniffer] >>> Handling new item Exception: {e}")

    def handle_new_character(self, params: dict):
        character_name = params.get(1)
        character_id = params.get(0)
        if character_name and isinstance(character_name, str):
            equipment = params.get(40)
            if equipment and isinstance(equipment, list):
                self.characters[character_id] = {"name": character_name, "equipment": equipment}

    def handle_silver_update(self, params: dict):
        silver = params.get(1)
        if silver is not None:
            try:
                silver_val = int(silver)
                with self.lock:
                    self.current_silver = int(f"{silver_val/10000:.0f}")
                    print(self.current_silver)
            except: pass

    def handle_read_mail(self, params: dict):
        mail_id = params.get(0)
        content_raw = params.get(1)
        if mail_id and content_raw:
            try:
                # If content_raw is already a string (decoded by Message), use it
                if isinstance(content_raw, str):
                    content_str = content_raw
                else:
                    if isinstance(content_raw, list): content_raw = bytes(content_raw)
                    content_str = content_raw.decode('utf-8', errors='ignore').replace('\x00', '')
                
                if '|' in content_str:
                    self.parse_smart_mail(mail_id, content_str)
            except: pass

    def parse_smart_mail(self, mail_id, content: str):
        parts = content.split('|')
        if len(parts) < 4: return
        data = {'mail_id': mail_id, 'timestamp': datetime.now(timezone.utc)}
        try:
            if len(parts[1]) > 2 and parts[0].replace('.', '').isdigit():
                data.update({
                    'transaction_type': "MARKETPLACE_FINISHED",
                    'amount': int(float(parts[0])),
                    'item_unique_name': parts[1],
                    'total_silver': int(float(parts[2])) // 10000,
                    'unit_price': int(float(parts[3])) // 10000
                })
                with self.lock: self.mail_buffer.append(data)
            elif len(parts[3]) > 2 and parts[1].replace('.', '').isdigit():
                data.update({
                    'transaction_type': "MARKETPLACE_EXPIRED",
                    'amount': int(float(parts[1])),
                    'item_unique_name': parts[3],
                    'total_silver': int(float(parts[2])) // 10000,
                    'unit_price': 0
                })
                with self.lock: self.mail_buffer.append(data)
        except Exception as e:
            print(f"[Sniffer] >>> Parsing mail Exception: {e}")

    def scan_for_market_data(self, params: dict | list | str):
        if isinstance(params, dict):
            if "ItemTypeId" in params and "UnitPriceSilver" in params:
                self.handle_market_order(params)
            else:
                for v in params.values(): self.scan_for_market_data(v)
        elif isinstance(params, list):
            for item in params: self.scan_for_market_data(item)
        elif isinstance(params, str):
            # Market data often comes as a JSON string inside the message
            if params.startswith('{') or params.startswith('['):
                try: self.scan_for_market_data(json.loads(params))
                except: pass

    def handle_market_order(self, params: dict):
        try:
            with self.lock:
                if params.get("AuctionType") == "offer":
                    self.offer_market_buffer.append(params)
                elif params.get("AuctionType") == "request":
                    self.request_market_buffer.append(params)
        except: pass

    def get_characters(self):
        with self.lock: return dict(self.characters)

    def get_equipment(self):
        with self.lock: return list(self.equipment)

    def get_inventory(self) -> dict:
        with self.lock: return dict(self.inventory)
        
    def clear_inventory(self):
        self.inventory.clear()

    def clear_market_buffer(self):
        self.offer_market_buffer.clear()
        self.request_market_buffer.clear()

    def get_market_buffer(self, type: str = None):
        with self.lock:
            offer_data = list(self.offer_market_buffer)
            request_data = list(self.request_market_buffer)
            self.offer_market_buffer.clear()
            self.request_market_buffer.clear()
        if type == "offer": return offer_data
        elif type == "request": return request_data
        return offer_data, request_data
    
    def get_mail_buffer(self):
        with self.lock:
            data = list(self.mail_buffer)
            self.mail_buffer.clear()
            return data
        
    def reset_session(self):
        with self.lock:
            self.inventory.clear()
            self.characters.clear()
            self.equipment = {}
            self.offer_market_buffer.clear()
            self.request_market_buffer.clear()
            self.mail_buffer.clear()
            self.frag_buffer.buffers.clear()
            self.frag_buffer = FragmentBuffer()
            self.layer_decoder = PhotonLayerDecoder()
        #print("[Sniffer] >>> Session & Network State Reset (Ready for New Account)")