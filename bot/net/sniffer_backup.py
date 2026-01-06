import socket
from scapy.all import get_if_list, get_if_addr, conf, sniff, UDP
import struct
import io
import gzip
import json
import threading
import os
import uuid
from datetime import datetime, timezone

# Import your local modules
from . import constants as const
from .layer import PhotonLayerDecoder
from .decoder import PhotonDataDecoder

# --- Constants from ZQRadar Analysis ---
class EventCodes:
    LEAVE = 1
    MOVE = 3
    JOIN_FINISHED = 2             # Initial Join
    NEW_CHARACTER = 29            # Player/Mob appeared
    INVENTORY_PUT_ITEM = 26       # Loot/Buy/Move (Add item to slot)
    INVENTORY_DELETE_ITEM = 27    # Sell/Trash/Move (Remove item from slot)
    INVENTORY_STATE = 28          # Full Inventory Sync
    CHARACTER_EQUIPMENT_CHANGED = 90

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
        self.lock = threading.Lock()
        
        # --- STATE ---
        self.current_silver = 0
        self.inventory = {}       # List of Dicts (The Bag)
        self.object_cache = {}
        self.equipment = {}       # The Paperdoll (Dict)
        self.players_nearby = {}

        # --- BUFFERS ---
        self.market_buffer = []
        self.offer_market_buffer = []
        self.request_market_buffer = []
        self.mail_buffer = []
        
        # --- DATA MAPPING ---
        self.item_map = {}
        self._load_item_names()

    def _load_item_names(self):
        """Loads items.json to map IDs (e.g. 75) to Names (e.g. T4_BAG)."""
        if self.item_map: return
        try:
            # Ensure items.json is in your working directory or provide full path
            path = 'items.json' 
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        # Handle both 'Index' and 'UniqueName' keys
                        idx = int(item.get('Index', item.get('id', -1)))
                        name = item.get('UniqueName', item.get('name', 'Unknown'))
                        if idx > 0: self.item_map[idx] = name
                print(f">>> [SYSTEM] Loaded {len(self.item_map)} item definitions.")
            else:
                print(">>> [SYSTEM] Warning: items.json not found. IDs will not be mapped.")
        except Exception as e:
            print(f">>> [SYSTEM] Error loading items.json: {e}")

    # --- CONTROL ---

    def start(self):
        iface = get_default_interface()
        print(f">>> Sniffer Started on Interface: {iface}")
        self.running = True
        
        while self.running:
            sniff(
                filter="udp port 5056", 
                iface=iface, 
                prn=self.packet_callback, 
                store=0,
                timeout=1 
            )
        print(">>> Sniffer Stopped")

    def stop(self):
        self.running = False

    # --- PACKET PROCESSING ---a

    def packet_callback(self, packet):
        if not self.running: return 
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
            op_code = 0

            # Message Type Logic
            if msg_type == 2:   # Operation Response
                op_code = ord(stream.read(1))
            elif msg_type == 3: # Operation Request
                op_code = ord(stream.read(1))
                stream.read(3) 
            elif msg_type == 4: # Event
                op_code = ord(stream.read(1))
            else: return

            params = PhotonDataDecoder(stream).decode()

            # --- ROUTING LOGIC ---
            self._scan_for_huge_inventory_array(params, op_code)
            # 1. Market Sell Tab (Operation Response)
            if msg_type == 2: 
                # We check every response for the specific "Sell List" structure
                if self._scan_for_market_sell_list(params):
                    return # Stop if found to save processing

            # 2. Events (Inventory, Equipment, Silver)
            if msg_type == 4:
                # Inventory State (Zone Join)
                event_code = params.get(252) # Event code is usually at 252 for Events
                if not event_code: event_code = op_code # Fallback

                if event_code in [29, 30, 31, 32, 35, 36, 37]: 
                    self._handle_new_item_definition(params)
                # 2. Main Inventory Load (Zone Join)
                elif event_code == EventCodes.INVENTORY_STATE:
                    self._handle_inventory_state(params)
                # 3. Item Moved/Added
                elif event_code == EventCodes.INVENTORY_PUT_ITEM:
                    self._handle_put_item(params)
                elif event_code == EventCodes.NEW_CHARACTER:
                    self._handle_new_character(params)
                # --- SINGLE ITEM UPDATES ---
                elif event_code == EventCodes.INVENTORY_DELETE_ITEM:
                    self._handle_inventory_delete_item(params)
                
                # Equipment
                elif event_code == EventCodes.CHARACTER_EQUIPMENT_CHANGED:
                    self._handle_equipment_change(params)

                # Silver
                elif event_code == const.OP_EVENT_UPDATE_SILVER:
                    self.handle_silver_update(params)

            # 3. Mail & Market Orders (Existing Logic)
            if op_code == const.OP_GET_MAIL_INFOS and 1 in params:
                self.handle_read_mail(params)
            
            self.scan_for_market_data(params)

        except Exception as e:
            print(f"Processing Error: {e}")

    # --- INVENTORY HANDLERS (NEW) ---

    def _handle_new_character(self, data):
        """
        Parses Event 29 (NewCharacter).
        This fires when ANY player or mob enters your vision.
        """
        char_name = data.get(1) # Usually Name
        char_id = data.get(0)   # Usually ID
        
        if char_name and isinstance(char_name, str):
            print(f">>> [ZONE] New Player/Mob: {char_name} (ID: {char_id})")
            
            equip_array = data.get(38) # Key 38 is typically equipment array
            if equip_array and isinstance(equip_array, list):
                print(f"    Wearing: {equip_array}")

    def _handle_equipment_change(self, data):
        """
        Parses Event 90.
        Your log shows: 0: UserID, 1: ?, 2: [ItemIDs...]
        """
        user_id = data.get(0)
        gear = data.get(2)
        
        if gear and isinstance(gear, list):
            # Map IDs to Names
            gear_names = [self.item_map.get(x, x) if x > 0 else "Empty" for x in gear]
            print(f">>> [EQUIP] User {user_id} Changed Gear:")
            print(f"    {gear_names}")

    def _handle_new_item_definition(self, data):
        """
        Parses NewSimpleItem, NewEquipmentItem, etc.
        Mapping: Key 0 = ObjectId, Key 1 = TypeId, Key 2 = Amount (sometimes)
        """
        try:
            obj_id = data.get(0)
            type_id = data.get(1)
            container_1 = data.get(8)
            container_2 = data.get(9)
            #print(data)
            
            if obj_id is not None and type_id is not None:
                name = self.item_map.get(type_id, f"ID_{type_id}")
                
                with self.lock:
                    self.object_cache[obj_id] = {"id": type_id, "name": name}
                
                # print(f">>> [CACHE] Learned Object {obj_id} = {name}")
            if type_id not in self.equipment:
                self.inventory[obj_id] = {"index": type_id}
        except: pass

    def _handle_inventory_state(self, data):
        """
        Parses the Master Inventory Packet (Event 28).
        This usually contains lists of Type IDs directly for the backpack.
        """
        ids = data.get(2) # Type IDs
        qtys = data.get(3) # Amounts
        
        if ids and qtys and isinstance(ids, list):
            # Scan for Backpack Range (usually 40-120)
            for i in range(len(ids)):
                if 40 <= i < 120 and ids[i] != 0:
                    name = self.item_map.get(ids[i], f"ID_{ids[i]}")
                    # Note: InventoryState gives TypeIDs directly, not ObjectIDs
                    # We can synthesize an object entry if needed, or just track inventory directly
                    pass
            #print(f">>> [SYNC] Inventory State Refreshed ({len(ids)} items)")

    def _handle_put_item(self, data):
        """
        Event 26: {0: ObjectId, 2: ContainerGUID, 3: Slot}
        """
        try:
            obj_id = data.get(0)
            container_guid_raw = data.get(2)
            slot = data.get(3)
            amount = data.get(1, 1)

            # 1. Resolve Container
            container_str = "Unknown"
            if container_guid_raw:
                container_str = str(uuid.UUID(bytes=bytes(container_guid_raw)))

            # 2. Resolve Item using Cache
            item_name = "Unknown Object"
            if obj_id in self.object_cache:
                info = self.object_cache[obj_id]
                item_name = info["name"]
            else:
                # Try simple signed/unsigned conversion fallback
                raw_id = obj_id
                if raw_id < 0: raw_id += 65536
                if raw_id in self.item_map:
                    item_name = self.item_map[raw_id]
                else:
                    item_name = f"Object {obj_id} (Missing Definition)"
            print(self.inventory)
            print(f">>> [INVENTORY] Slot {slot} | {item_name} (x{amount})")
            #print(f"    Container: {container_str}")
            print(data)

        except Exception as e:
            print(f"PutItem Error: {e}")

    def _handle_inventory_delete_item(self, data):
        """
        Handles Event 27: Item Removed.
        """
        #print(f">>> [INVENTORY] Delete Item (Update): {data}")
        # TODO: Implement deletion logic once structure is verified from logs

    def _scan_for_huge_inventory_array(self, data, op_code):
        """
        The "God Mode" scanner. 
        It ignores Event Codes and looks for the Data Structure directly.
        Target: Length > 100 parallel arrays.
        """
        ids = data.get(2)
        qtys = data.get(3)

        if ids and qtys and isinstance(ids, list) and isinstance(qtys, list):
            if len(ids) > 100: # It's the Master List (Bank + Bag)
                if len(ids) == len(qtys):
                    
                    new_bag = []
                    # Filter for Backpack slots (approx 40-100 based on your logs)
                    for i in range(40, min(120, len(ids))):
                        t_id = ids[i]
                        amount = qtys[i]
                        
                        if t_id != 0:
                            name = self.item_map.get(t_id, f"ID_{t_id}")
                            new_bag.append({"name": name, "amount": amount, "id": t_id})
                    
                    with self.lock:
                        #self.inventory = new_bag
                        pass
                    
                    #print(f">>> [SYNC] FULL INVENTORY FOUND (Op/Event {op_code})")
                    # print(data) # Uncomment to debug raw packet if needed

    def _handle_inventory_state(self, data):
        """
        Parses Event 28 (InventoryState).
        Uses the 'Master Packet' logic with Range Filtering for the Backpack.
        """
        ids_list = data.get(2) # Key 2 = IDs
        qty_list = data.get(3) # Key 3 = Quantities

        # Basic Validation
        if not ids_list or not qty_list: return
        if not isinstance(ids_list, list) or len(ids_list) < 50: return 

        new_bag = []
        
        # --- CONFIGURATION: BACKPACK RANGE ---
        START_INDEX = 40
        END_INDEX = 120 

        for i in range(len(ids_list)):
            if i < START_INDEX or i > END_INDEX: continue

            t_id = ids_list[i]
            amount = qty_list[i]

            if t_id != 0:
                name = self.item_map.get(t_id, f"Item_{t_id}")
                new_bag.append({
                    "slot": i - START_INDEX,
                    "id": t_id,
                    "name": name,
                    "amount": amount
                })

        with self.lock:
            #self.inventory = new_bag
            pass
            
        #print(f">>> [SYNC] Passive Inventory Update (Event 28). Found {len(new_bag)} items.")

    def _scan_for_market_sell_list(self, data):
        """
        Parses the Market Sell Tab Response.
        """
        candidates = []
        if isinstance(data, dict):
            candidates = [v for v in data.values() if isinstance(v, list)]
        elif isinstance(data, list):
            candidates = [data]

        for main_list in candidates:
            if not main_list: continue
            
            # Filter out UI noise using strict length checks
            first_item = main_list[0]
            if not isinstance(first_item, list) or len(first_item) < 6:
                continue

            if isinstance(first_item[0], int) and isinstance(first_item[1], int):
                new_bag = []
                for i, item_data in enumerate(main_list):
                    t_id = item_data[0]
                    amount = item_data[1]
                    name = self.item_map.get(t_id, f"Item_{t_id}")
                    
                    new_bag.append({
                        "slot": i,
                        "id": t_id,
                        "name": name,
                        "amount": amount
                    })
                
                with self.lock:
                    #self.inventory = new_bag
                    pass
                    
                #print(f">>> [MARKET] Active Inventory Update (Sell Tab). Found {len(new_bag)} items.")
                return True
        return False

    # --- EXISTING HANDLERS (Unchanged logic) ---

    def handle_silver_update(self, params):
        silver = params.get(1)
        if silver is not None:
            try:
                silver_val = int(silver)
                with self.lock:
                    self.current_silver = int(f"{silver_val/10000:.0f}")
            except: pass

    def handle_read_mail(self, params):
        mail_id = params.get(0)
        content_raw = params.get(1)
        if mail_id and content_raw:
            try:
                if isinstance(content_raw, list): content_raw = bytes(content_raw)
                content_str = content_raw.decode('utf-8', errors='ignore').replace('\x00', '')
                if '|' in content_str:
                    self.parse_smart_mail(mail_id, content_str)
            except: pass

    def parse_smart_mail(self, mail_id, content):
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
        except: pass

    def scan_for_market_data(self, data):
        if isinstance(data, dict):
            if "ItemTypeId" in data and "UnitPriceSilver" in data:
                self._handle_market_order(data)
            else:
                for v in data.values(): self.scan_for_market_data(v)
        elif isinstance(data, list):
            for item in data: self.scan_for_market_data(item)
        elif isinstance(data, str):
            if data.startswith('{') or data.startswith('['):
                try: self.scan_for_market_data(json.loads(data))
                except: pass

    def _handle_market_order(self, order):
        try:
            with self.lock:
                if order.get("AuctionType") == "offer":
                    self.offer_market_buffer.append(order)
                elif order.get("AuctionType") == "request":
                    self.request_market_buffer.append(order)
        except: pass

    # --- PUBLIC GETTERS ---

    def get_inventory(self):
        with self.lock:
            return dict(self.inventory)

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

if __name__ == "__main__":
    sniffer = AlbionSniffer()
    try:
        sniffer.start()
    except KeyboardInterrupt:
        sniffer.stop()