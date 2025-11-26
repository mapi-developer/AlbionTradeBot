# net/sniffer.py
from scapy.all import sniff, UDP, conf
from .photon_layer import PhotonLayerDecoder
from photon.decoder import PhotonDataDecoder
import photon.constants as const
import json
import struct
import io

class FragmentBuffer:
    def __init__(self):
        self.buffers = {}

    def handle_fragment(self, payload):
        # Ref: ReliableFragment in Go
        # Seq(4), Count(4), Num(4), TotalLen(4), Offset(4)
        if len(payload) < 20:
            return None

        # Using >i (signed int) to match Go's int32
        seq_id, frag_count, frag_num, total_len, offset = struct.unpack(">iiiii", payload[:20])
        data = payload[20:]

        if seq_id not in self.buffers:
            self.buffers[seq_id] = {
                "count": frag_count,
                "parts": {},
                "total_len": total_len
            }

        self.buffers[seq_id]["parts"][frag_num] = data

        # Check completion
        if len(self.buffers[seq_id]["parts"]) == frag_count:
            return self._reassemble(seq_id)
        return None

    def _reassemble(self, seq_id):
        buf = self.buffers.pop(seq_id)
        ordered_data = b""
        for i in range(buf["count"]):
            ordered_data += buf["parts"][i]
        return ordered_data

class AlbionSniffer:
    def __init__(self):
        self.layer_decoder = PhotonLayerDecoder()
        self.frag_buffer = FragmentBuffer()

    def packet_callback(self, packet):
        if not packet.haslayer(UDP): return
        
        # Albion Port
        if packet[UDP].sport != 5056 and packet[UDP].dport != 5056: return

        try:
            payload = bytes(packet[UDP].payload)
            commands = self.layer_decoder.decode_packet(payload)

            for cmd in commands:
                if cmd.type == const.COMMAND_SEND_RELIABLE:
                    self.process_reliable_message(cmd.payload)
                
                elif cmd.type == const.COMMAND_SEND_FRAGMENT:
                    full_msg = self.frag_buffer.handle_fragment(cmd.payload)
                    if full_msg:
                        self.process_reliable_message(full_msg)
                        
        except Exception:
            pass

    def process_reliable_message(self, payload):
        """
        Decodes the Reliable Message Header.
        Header Format: Signature(1) + Type(1) + [OpCode(1) + ... params]
        """
        stream = io.BytesIO(payload)
        
        # 1. Signature
        stream.read(1)
        
        # 2. Message Type
        type_byte = stream.read(1)
        if not type_byte: return
        msg_type = ord(type_byte)

        # We care about OperationResponse (Type 3 or 7)
        if msg_type == 2: 
            return # Request
            
        elif msg_type in [3, 7]: 
            # Operation Response
            op_code = ord(stream.read(1))
            stream.read(2) # Return Code (Int16)
            
            # Debug String: Go reads this as a Photon Type.
            # We use our decoder to safely consume/skip it.
            # It is usually Type Nil (42) or String (115).
            debug_type_byte = stream.read(1)
            if not debug_type_byte: return
            debug_type = ord(debug_type_byte)
            
            # If it's not Nil, we must read the value so the stream position advances correctly
            if debug_type != const.TYPE_NIL:
                # Reset stream back 1 byte so decoder can read the Type+Value combo
                stream.seek(-1, 1) 
                PhotonDataDecoder(stream).decode_type(debug_type)
            
            # Now we are at the Dictionary
            self.decode_dictionary(op_code, stream)

    def decode_dictionary(self, op_code, stream):
        decoder = PhotonDataDecoder(stream)
        params = decoder.decode()
        
        # Parameter 253 often contains the true Operation Code in some versions,
        # but for Market Data, we look for Parameter 0 which is the JSON payload.
        if 0 in params:
            self.handle_market_data(params[0])

    def handle_market_data(self, data_obj):
        # Data can be a single JSON string or a list of strings
        if isinstance(data_obj, str):
            self.parse_json(data_obj)
        elif isinstance(data_obj, list):
            for s in data_obj:
                if isinstance(s, str):
                    self.parse_json(s)

    def parse_json(self, json_str):
        try:
            data = json.loads(json_str)
            # Verify it's a market order by checking specific keys
            if "ItemTypeId" in data and "UnitPriceSilver" in data:
                print(f"[MARKET] {data['ItemTypeId']} | Price: {data['UnitPriceSilver']} | Amt: {data['Amount']} | Loc: {data.get('LocationId')}")
        except json.JSONDecodeError:
            pass

    def start(self, interface=None):
        print("Sniffer Started. Waiting for Market Data...")
        if interface:
            sniff(filter="udp port 5056", prn=self.packet_callback, store=0, iface=interface)
        else:
            sniff(filter="udp port 5056", prn=self.packet_callback, store=0)