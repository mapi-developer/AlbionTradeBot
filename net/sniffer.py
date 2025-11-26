from scapy.all import sniff, UDP
from .photon_layer import PhotonLayerDecoder
from photon.decoder import PhotonDataDecoder
import json

class AlbionSniffer:
    def __init__(self):
        self.layer_decoder = PhotonLayerDecoder()

    def packet_callback(self, packet):
        if not packet.haslayer(UDP):
            return

        # Check port (Source or Dest should be 5056)
        if packet[UDP].sport != 5056 and packet[UDP].dport != 5056:
            return

        try:
            raw_payload = bytes(packet[UDP].payload)
            commands = self.layer_decoder.decode_packet(raw_payload)

            for cmd in commands:
                # Photon Command Type 1 is usually Operation Request/Response
                if cmd.type == 1: 
                    self.process_operation(cmd.payload)
        except Exception as e:
            # Packet processing errors are common in sniffing (fragmentation, etc.)
            pass

    def process_operation(self, payload):
        # Use the decoder to extract the dictionary
        decoder = PhotonDataDecoder(payload)
        params = decoder.decode()
        
        # The key '253' usually holds the Operation Code (int16)
        # Ref: decode.go -> code := params[253].(int16)
        op_code = params.get(253)
        
        if op_code:
            self.on_operation_received(op_code, params)

    def on_operation_received(self, op_code, params):
        # Logic from 'operation_auction_get_offers.go'
        # Parameter 0 usually contains the JSON string for market data
        if 0 in params:
            data_str = params[0]
            # Sometimes data comes as a list of strings or a single string
            if isinstance(data_str, list):
                for item in data_str:
                    self.parse_market_json(item)
            elif isinstance(data_str, str):
                self.parse_market_json(data_str)

    def parse_market_json(self, json_str):
        try:
            data = json.loads(json_str)
            # Filter for valid market orders
            if "ItemTypeId" in data and "UnitPriceSilver" in data:
                print(f"MARKET: {data['ItemTypeId']} | Price: {data['UnitPriceSilver']} | Amount: {data['Amount']}")
        except json.JSONDecodeError:
            pass

    def start(self):
        print("Starting Albion Market Sniffer on UDP 5056...")
        # 'store=0' prevents RAM issues by not keeping packet history
        sniff(filter="udp port 5056", prn=self.packet_callback, store=0)