# layer.py
import struct

class PhotonCommand:
    def __init__(self, cmd_type, channel_id, flags, reserved_byte, length, sequence_number, payload):
        self.type = cmd_type
        self.channel_id = channel_id
        self.flags = flags
        self.reserved_byte = reserved_byte
        self.length = length
        self.sequence_number = sequence_number
        self.payload = payload

class PhotonLayerDecoder:
    def decode_packet(self, data: bytes):
        if len(data) < 12: return []

        # Photon Header: PeerID(2), Crc(1), CmdCount(1), Timestamp(4), Challenge(4)
        cmd_count = struct.unpack(">HBBIi", data[:12])[2]
        
        commands = []
        offset = 12
        
        for _ in range(cmd_count):
            if offset + 12 > len(data): break
            
            # Command Header: Type(1), Channel(1), Flags(1), Rsv(1), Len(4), Seq(4)
            cmd_header = data[offset:offset+12]
            (
                cmd_type, 
                channel_id, 
                flags, 
                reserved_byte, 
                length, 
                sequence_number
            ) = struct.unpack(">BBBBII", cmd_header)
            
            payload_size = length - 12
            start = offset + 12
            end = start + payload_size
            
            if end > len(data): break
            
            payload = data[start:end]
            
            commands.append(PhotonCommand(
                cmd_type, 
                channel_id, 
                flags, 
                reserved_byte, 
                length, 
                sequence_number, 
                payload
            ))
            
            offset = end
            
        return commands