from scapy.all import sniff, UDP, conf
from .photon_layer import PhotonLayerDecoder
from photon.decoder import PhotonDataDecoder
import json
import sys

class AlbionSniffer:
    def __init__(self):
        self.layer_decoder = PhotonLayerDecoder()

    def packet_callback(self, packet):
        # DEBUG: Print that a packet arrived (comment this out later if too noisy)
        # print(f"Packet captured: {packet.summary()}")

        if not packet.haslayer(UDP):
            return

        # Check port (Source or Dest should be 5056)
        if packet[UDP].sport != 5056 and packet[UDP].dport != 5056:
            return

        # DEBUG: We found an Albion Packet
        # print(f"Albion Packet detected! Len: {len(packet[UDP].payload)}")

        try:
            raw_payload = bytes(packet[UDP].payload)
            commands = self.layer_decoder.decode_packet(raw_payload)

            for cmd in commands:
                # Photon Command Type 1 is usually Operation Request/Response
                if cmd.type == 1: 
                    self.process_operation(cmd.payload)
                else:
                    # DEBUG: See other command types (Type 6/7 are reliable/unreliable messaging)
                    # print(f"Ignored Command Type: {cmd.type}")
                    pass

        except Exception as e:
            print(f"[Error processing packet]: {e}")

    def process_operation(self, payload):
        try:
            decoder = PhotonDataDecoder(payload)
            params = decoder.decode()
            
            # The key '253' usually holds the Operation Code (int16)
            op_code = params.get(253)
            print(payload)
            # DEBUG: Print every operation code received to find the Market one
            if op_code:
                print(f"Operation Code Received: {op_code}")
                self.on_operation_received(op_code, params)
        except Exception as e:
            print(f"[Error decoding operation]: {e}")

    def on_operation_received(self, op_code, params):
        # Check if Parameter 0 exists (Market Data)
        if 0 in params:
            data_str = params[0]
            print(f"--> Market Data Found in OP {op_code}!")
            
            if isinstance(data_str, list):
                for item in data_str:
                    self.parse_market_json(item)
            elif isinstance(data_str, str):
                self.parse_market_json(data_str)

    def parse_market_json(self, json_str):
        try:
            data = json.loads(json_str)
            if "ItemTypeId" in data and "UnitPriceSilver" in data:
                print(f"MARKET: {data['ItemTypeId']} | Price: {data['UnitPriceSilver']} | Amount: {data['Amount']}")
        except json.JSONDecodeError:
            print(f"[Error] Failed to decode JSON: {json_str[:50]}...")

    def start(self, interface=None):
        print("Starting Albion Market Sniffer on UDP 5056...")
        print("Press Ctrl+C to stop.")
        
        if interface:
            print(f"Listening on interface: {interface}")
            # 'store=0' prevents RAM issues by not keeping packet history
            sniff(filter="udp port 5056", prn=self.packet_callback, store=0, iface=interface)
        else:
            print("Listening on default interface (Check if this is correct for Windows)...")
            print(f"Default Interface: {conf.iface}")
            sniff(filter="udp port 5056", prn=self.packet_callback, store=0)