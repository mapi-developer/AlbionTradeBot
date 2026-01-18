from typing import Callable
from scapy.all import get_if_list, get_if_addr, conf, sniff, UDP, Packet
import gzip
import json
import io
import socket
import threading

from ..classes.player import LocalPlayer, Equipment
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
    def __init__(self, local_player: LocalPlayer):
        self.local_player = local_player
        self.lock = threading.Lock()
        self.frag_buffer = FragmentBuffer()

        self.on_silver_changed = []
        self.on_local_position_changed = []
        self.on_location_changed = []
        self.on_local_player_nickname_changed = []
        self.on_equipment_changed = []
        self.on_join_finished = []
        self.on_new_item = []

        self.request_market_buffer = []
        self.offer_market_buffer = []
        self.characters = {}
        self.last_avg_price = 0

        self.running = False

    def subscribe_new_item(self, callback: Callable):
        with self.lock:
            if callback not in self.on_new_item:
                self.on_new_item.append(callback)

    def subscribe_silver(self, callback: Callable):
        with self.lock:
            if callback not in self.on_silver_changed:
                self.on_silver_changed.append(callback)

    def subscribe_position(self, callback: Callable):
        with self.lock:
            if callback not in self.on_local_position_changed:
                self.on_local_position_changed.append(callback)

    def subscribe_location(self, callback: Callable):
        with self.lock:
            if callback not in self.on_location_changed:
                self.on_location_changed.append(callback)

    def subscribe_nickname(self, callback: Callable):
        with self.lock:
            if callback not in self.on_local_player_nickname_changed:
                self.on_local_player_nickname_changed.append(callback)

    def subscribe_equipment(self, callback: Callable):
        with self.lock:
            if callback not in self.on_equipment_changed:
                self.on_equipment_changed.append(callback)

    def subscribe_join(self, callback: Callable):
        with self.lock:
            if callback not in self.on_join_finished:
                self.on_join_finished.append(callback)

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
        try: 
            payload = gzip.decompress(payload)
        except (OSError, EOFError):
            pass

        try:
            stream = io.BytesIO(payload)
            msg = ReliableMessage.unpack(stream)
            if not msg: return

            params = msg.decode()
            
            if 253 in params:
                request_code = params.get(253)
                if request_code in [const.OP_AUCTION_GET_REQUESTS, const.OP_AUCTION_GET_MY_ORDERS]:
                    self.handle_market_orders(params, "request")
                elif request_code == const.OP_AUCTION_GET_OFFERS:
                    self.handle_market_orders(params, "offer")    
                elif request_code == const.OP_MOVE_REQUEST:
                    self.handle_local_move(params)
                elif request_code == const.OP_JOIN_FINISHED:
                    # 8 current location, 9 previous location
                    self.handle_local_player_info_changed(params)
                elif request_code == const.OP_LOCATION_CHANGED:
                    self.handle_location_changed(params)
                elif request_code == const.OP_AUCTION_AVG_GET:
                    self.handle_avg_market_data(params)
                else:
                    return
            elif 252 in params:
                event_code = params.get(252)
                if event_code == const.OP_EVENT_UPDATE_SILVER:
                    self.handle_silver_update(params)
                elif event_code == const.EVENT_NEW_ITEM:
                    self.handle_new_item(params)
                elif event_code == const.OP_NEW_CHARACTER:
                    self.handle_new_character(params)
                elif event_code == const.OP_CHARACTER_EQUIPMENT_CHANGED:
                    self.handle_equipment_changed(params)
                else: return 
            else:
                return 
        except Exception as e:
            pass

    def handle_avg_market_data(self, params: dict):
        price_sum = sum(params.get(1))
        amount_sum = sum(params.get(0))
        if price_sum == None or amount_sum == None:
            self.last_avg_price = 0
        self.last_avg_price = int(price_sum/amount_sum/10000)

    def handle_new_character(self, params: dict):
        character_name = params.get(1)
        character_id = params.get(0)
        if character_name and isinstance(character_name, str):
            equipment = params.get(40)
            if equipment and isinstance(equipment, list):
                self.characters[character_id] = {"name": character_name, "equipment": equipment}

    def handle_equipment_changed(self, params: dict):
        user_id = params.get(0)
        equipment = params.get(2)
        if equipment and isinstance(equipment, list):
            if user_id in self.characters.keys():
                self.characters[user_id] = equipment
            else:
                self.local_player.equipment.from_list(equipment)

    def handle_new_item(self, params: dict):
        try:
            local_item_id = params.get(0)
            item_index = params.get(1)
            if local_item_id is not None and item_index is not None:
                with self.lock:
                    if item_index not in self.local_player.equipment.to_list():
                        for callback in self.on_new_item:
                            callback(local_item_id, item_index, "inventory")

        except Exception as e:
            print(f"[Sniffer] >>> Handling new item Exception: {e}")

    def handle_location_changed(self, params: dict):
        self.characters = {}
        self.local_player.clear_inventory()
        self.local_player.equipment.clear()
        location_id = params.get(0)
        location_type = params.get(1, '')
        location_name = params.get(2, '')
        if location_type == '' and location_name == []: return
        for callback in self.on_location_changed:
            callback(location_id, location_type, location_name)

    def handle_local_player_info_changed(self, params: dict):
        local_nickname = params.get(2)
        local_id = params.get(0)
        local_silver_balance = params.get(32)
        local_position = params.get(9)
        self.handle_silver_update({1: local_silver_balance})
        self.handle_local_move({1: local_position})
        for callback in self.on_local_player_nickname_changed:
            callback(local_nickname, local_id)
        for callback in self.on_join_finished:
            callback(True)
        
    def handle_local_move(self, params: dict):
        current_position = params.get(1)
        # print(f"   {current_position}", end = "               \r", flush=True)
        for callback in self.on_local_position_changed:
            callback(current_position)

    def handle_silver_update(self, params: dict):
        silver = params.get(1)
        if silver is None: return
        try:
            silver_value = int(silver)//10000
            with self.lock:
                for callback in self.on_silver_changed:
                    callback(silver_value)
        except: pass

    def handle_market_orders(self, params: dict, order_type: str):
        market_orders = [json.loads(item) for item in params.get(0)]
        if market_orders is None or not isinstance(market_orders, list): return
        try:
            with self.lock:
                if order_type == "offer":
                    self.offer_market_buffer.extend(market_orders)
                else:
                    self.request_market_buffer.extend(market_orders)
        except: pass

    def get_last_avg_price(self):
        with self.lock:
            last_avg_price = self.last_avg_price
            self.last_avg_price = 0
            return last_avg_price

    def clear_market_buffers(self):
        self.offer_market_buffer.clear()
        self.request_market_buffer.clear()

    def get_market_buffers(self, buffer_type: str = None) -> list[dict] | tuple[list[dict], list[dict]]:
        with self.lock:
            offer_data = list(self.offer_market_buffer)
            request_data = list(self.request_market_buffer)
            self.clear_market_buffers()
        if buffer_type == "offer": return offer_data
        elif buffer_type == "request": return request_data
        return offer_data, request_data