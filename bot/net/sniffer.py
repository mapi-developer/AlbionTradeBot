import gzip
import io
import struct
import socket
import threading
import json
from datetime import datetime, timezone
from scapy.all import get_if_list, get_if_addr, conf, sniff, UDP

from . import constants as const
from .layer import PhotonLayerDecoder
from .decoder import PhotonDataDecoder


def get_default_interface():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return [i for i in get_if_list() if get_if_addr(i) == s.getsockname()[0]][0]
    except: return conf.iface


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
    

class AlbionSniffer:
    def __init__(self):
        self.layer_decoder = PhotonLayerDecoder()
        self.frag_buffer = FragmentBuffer()
        self.running = False
        self.lock = threading.Lock()

        self.current_silver = 0
        self.characters = {}
        self.inventory = {}
        self.equipment = {}

        self.offer_market_buffer = []
        self.request_market_buffer = []
        self.mail_buffer = []
        
    def start(self):
        iface = get_default_interface()
        print(f"[Sniffer] >>> Started on Interface: {iface}")
        self.running = True

        while self.running:
            sniff(
                filter="udp port 5056",
                iface=iface,
                prn=self.packet_callback,
                store=0,
                timeout=1
            )
        print(f"[Sniffer] >>> Stoped.")

    def stop(self):
        self.running = False

    def packet_callback(self, packet):
        if not self.running: return
        if not packet.haslayer(UDP): return
        try:
            for cmd in self.layer_decoder.decode_packet(bytes(packet[UDP].payload)):
                if cmd.type == const.COMMAND_SEND_RELIABLE:
                    self.process(cmd.payload)
                elif cmd.type == const.COMMAND_SEND_FRAGMENT:
                    msg = self.frag_buffer.handle(cmd.payload)
                    if msg: self.process(msg)
        except Exception as e:
            print(f"[Sniffer] >>> Packet Callback Exception: {e}")

    def process(self, payload):
        if payload[:2] == b'\x1f\x8b':
            try: payload = gzip.decompress(payload)
            except: return

        try:
            if len(payload) < 3: return
            msg_type, op_code = payload[1], payload[2]

            if msg_type == 3:
                offset = 6
            elif msg_type in (2, 4):
                offset = 3
            else:
                return

            stream = io.BytesIO(payload[offset:])
            params = PhotonDataDecoder(stream).decode()

            if msg_type == 4:
                event_code = params.get(252)
                if not event_code: event_code = op_code

                elif event_code == const.OP_CHARACTER_EQUIPMENT_CHANGED:
                    self.handle_equipment_changed(params)
                elif event_code == const.EVENT_NEW_ITEM:
                    self.handle_new_item(params)
                elif event_code == const.OP_NEW_CHARACTER:
                    self.handle_new_character(params)
                elif event_code == const.OP_EVENT_UPDATE_SILVER:
                    self.handle_silver_update(params)
            elif msg_type == 2:
                event_code = params.get(252)
                # print(params)
                if event_code == 2:
                    self.handle_join_response(params)
            elif op_code == const.OP_GET_MAIL_INFOS and 1 in params:
                self.handle_read_mail(params)

            self.scan_for_market_data(params)
        except Exception as e:
            print(f"[Sniffer] >>> Processing Exception: {e}")

    def handle_join_response(self, params: dict):
        try:
            if 0 in params:
                self.local_player_id = params[0]
                # print(f"[Sniffer] >>> Join Complete! Local Player ID: {self.local_player_id}")
            if 2 in params:
                self.character_name = params[2]
                # print(f"[Sniffer] >>> Character Name: {self.character_name}")
        except Exception as e:
            print(f"[Sniffer] >>> Handle Join Error: {e}")

    def handle_equipment_changed(self,  params: dict):
        user_id = params.get(0)
        equipment = params.get(2)

        if equipment and isinstance(equipment, list):
            equipment_names = [x if x > 0 else None for x in equipment]
            # print(f"[Sniffer] >>> User {user_id} equipment changed:")
            # print(f"[Sniffer] >>> Equipment: {equipment_names}")
            
            if user_id in self.characters.keys():
                self.characters[user_id] = equipment
            else:
                self.equipment = equipment


    def handle_new_item(self, params: dict):
        try:
            # print(params)
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
            # print(f"[Sniffer] >>> New Player/Mob: {character_name}")
            equipment = params.get(40)
            if equipment and isinstance(equipment, list):
                # print(f"[Sniffer] >>> Equipment: {equipment}")
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

    # PUBLIC FUNCTIONS

    def get_characters(self):
        with self.lock:
            return dict(self.characters)

    def get_equipment(self):
        with self.lock:
            return list(self.equipment)

    def get_inventory(self) -> dict:
        with self.lock:
            inventory_data = dict(self.inventory)
            return inventory_data
        
    def clear_inventory(self):
        self.inventory.clear()

    def get_market_buffer(self, type: str = None):
        with self.lock:
            offer_data = list(self.offer_market_buffer)
            request_data = list(self.request_market_buffer)
            self.offer_market_buffer.clear()
            self.request_market_buffer.clear()

        print(self.offer_market_buffer)
        print(self.request_market_buffer)
            
        if type == "offer": return offer_data
        elif type == "request": return request_data
        return offer_data, request_data
    
    def get_mail_buffer(self):
        with self.lock:
            data = list(self.mail_buffer)
            self.mail_buffer.clear()
            return data
        
    def reset_session(self):
        """
        Clears all session-specific data AND resets network decoders.
        """
        with self.lock:
            # 1. Clear Data Buffers
            self.inventory.clear()
            self.characters.clear()
            self.equipment = {}
            self.offer_market_buffer.clear()
            self.request_market_buffer.clear()
            self.mail_buffer.clear()

            # 2. CRITICAL: Reset Network State
            # The new session starts with Sequence Number 0. 
            # We must recreate the decoder so it accepts them.
            self.frag_buffer = FragmentBuffer()
            self.layer_decoder = PhotonLayerDecoder()
            
        print("[Sniffer] >>> Session & Network State Reset (Ready for New Account)")