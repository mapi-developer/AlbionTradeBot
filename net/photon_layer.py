# net/photon_layer.py
import struct

class PhotonCommand:
    def __init__(self, cmd_type, channel_id, flags, length, seq_num, payload):
        self.type = cmd_type
        self.channel_id = channel_id
        self.flags = flags
        self.length = length
        self.seq_num = seq_num
        self.payload = payload

class PhotonLayerDecoder:
    def decode_packet(self, data: bytes):
        if len(data) < 12:
            return []

        # Header: PeerID(2), Crc(1), CmdCount(1), Timestamp(4), Challenge(4)
        # >HBBIi matches Go logic
        peer_id, crc, cmd_count, timestamp, challenge = struct.unpack(">HBBIi", data[:12])
        
        commands = []
        offset = 12
        
        for _ in range(cmd_count):
            if offset + 12 > len(data):
                break
            
            # Command Header: Type(1), Channel(1), Flags(1), Rsv(1), Len(4), Seq(4)
            cmd_type, channel, flags, rsv, length, seq = struct.unpack(">BBBBII", data[offset:offset+12])
            
            # The 'length' includes the 12-byte header
            payload_size = length - 12
            
            start = offset + 12
            end = start + payload_size
            
            if end > len(data):
                break
                
            command_payload = data[start:end]
            
            commands.append(PhotonCommand(cmd_type, channel, flags, length, seq, command_payload))
            offset = end
            
        return commands