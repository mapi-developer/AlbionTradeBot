import gzip
import io
import threading
import json
import socket
from datetime import datetime, timezone
from scapy.all import get_if_list, get_if_addr, conf, sniff, UDP

# Local Imports
from . import constants as const
from .graph import WaypointGraph

# New Photon Imports (Local)
from .photon_command import PhotonLayer
from .reliable_message import ReliableMessage, EventDataType, OperationRequest, OperationResponse
from .fragment_buffer import FragmentBuffer
from .enums import CommandType, MessageType

def get_default_interface():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return [i for i in get_if_list() if get_if_addr(i) == s.getsockname()[0]][0]
    except:
        return conf.iface

class AlbionSniffer:
    def __init__(self):
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
        self.travel_planner_point = None

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
        return list(self.current_position) if self.current_position else None

    def packet_callback(self, packet):
        if not self.running: return
        if not packet.haslayer(UDP): return

        try:
            payload = bytes(packet[UDP].payload)
            # Use local PhotonLayer to unpack
            layer = PhotonLayer.unpack(io.BytesIO(payload))
            
            for cmd in layer.commands:
                if cmd.type == CommandType.SendReliableType:
                    self.process(cmd.data)
                    
                elif cmd.type == CommandType.SendReliableFragmentType:
                    try:
                        frag = cmd.reliable_fragment()
                        # Buffer returns a reassembled BasePhotonCommand if complete
                        reassembled_cmd = self.frag_buffer.offer(frag)
                        if reassembled_cmd:
                            self.process(reassembled_cmd.data)
                    except Exception as e:
                        print(f"[Sniffer] Fragment Error: {e}")
                        
        except Exception:
            pass

    def process(self, payload):
        # Handle GZIP
        if payload.startswith(b'\x1f\x8b'):
            try: 
                payload = gzip.decompress(payload)
            except: 
                return

        try:
            stream = io.BytesIO(payload)
            msg = ReliableMessage.unpack(stream)
            if not msg:
                return

            params = msg.decode()
            
            op_code = 0
            event_code = 0

            # Determine Codes
            if isinstance(msg, OperationRequest):
                op_code = msg.operation_code
            elif isinstance(msg, OperationResponse):
                op_code = msg.operation_code
            elif isinstance(msg, EventDataType):
                event_code = msg.event_code

            # --- Albion Logic ---
           #print(params)
            # 1. Multi-Move / Position Updates
            #print(params)
            print(f"Position: {self.current_position}", flush=True, end = "              \r")
            if params.get(252) == const.EVENT_NEW_TRAVEL_POINT:
                if "FASTTRAVEL_POINT" in params.get(3):
                    self.travel_planner_point = params.get(1)
                    
            if 253 in params:
                # 253 often contains the "real" opcode for move requests
                op_code = params[253]
                if op_code == const.OP_MOVE_REQUEST:
                    current_pos = params.get(1) # List [x, y]
                    if current_pos is not None:
                        self.current_position = current_pos
                        #print(f"Position: {self.current_position}")
                        #print(params)
                elif op_code == const.OP_JOIN_FINISHED:
                    current_pos = params.get(9)
                    if current_pos is not None:
                        self.current_position = current_pos

            # 2. Events
            elif msg.type == MessageType.EventDataType:
                sub_code = params.get(252)
                
                if event_code == const.OP_CHARACTER_EQUIPMENT_CHANGED:
                    self.handle_equipment_changed(params)
                elif event_code == const.EVENT_NEW_ITEM:
                    self.handle_new_item(params)
                elif event_code == const.OP_NEW_CHARACTER:
                    self.handle_new_character(params)
                elif event_code == const.OP_EVENT_UPDATE_SILVER:
                    self.handle_silver_update(params)
                
                if sub_code == 2: # Join Response
                    self.handle_join_response(params)

            # 3. Operations
            elif msg.type in (MessageType.OperationRequest, MessageType.OperationResponse, MessageType.otherOperationResponse):
                if op_code == 2: # Join Request Response
                     self.handle_join_response(params)
                
                elif op_code == const.OP_GET_MAIL_INFOS and 1 in params:
                    self.handle_read_mail(params)

            # 4. Market Data Scan
            self.scan_for_market_data(params)

        except Exception as e:
            pass

    # --- Handlers (Unchanged logic) ---

    def handle_join_response(self, params: dict):
        try:
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
            except: pass

    def handle_read_mail(self, params: dict):
        mail_id = params.get(0)
        content_raw = params.get(1)
        if mail_id and content_raw:
            try:
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

    def scan_for_market_data(self, params):
        if isinstance(params, dict):
            if "ItemTypeId" in params and "UnitPriceSilver" in params:
                self.handle_market_order(params)
            else:
                for v in params.values(): self.scan_for_market_data(v)
        elif isinstance(params, list):
            for item in params: self.scan_for_market_data(item)
        elif isinstance(params, str):
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
            self.frag_buffer = FragmentBuffer()