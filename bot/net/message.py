import io
import struct

# Constants / Enums
class ReliableMessageType:
    Nil = 42
    Dictionary = 68
    StringArray = 97
    Int8 = 98
    Double = 100
    EventData = 101
    Float32 = 102
    Hashtable = 104
    Int32 = 105
    Int16 = 107
    Int64 = 108
    Int32Array = 110
    Boolean = 111
    OperationResponse = 112
    OperationRequest = 113
    String = 115
    Int8Array = 120
    Array = 121
    ObjectArray = 122

class MessageType:
    OperationRequest = 2
    OtherOperationResponse = 3
    EventData = 4
    OperationResponse = 7

def decode_type(buf: io.BytesIO, param_type: int):
    if param_type in (ReliableMessageType.Nil, 0):
        return None
    elif param_type == ReliableMessageType.Int8:
        return struct.unpack(">b", buf.read(1))[0]
    elif param_type == ReliableMessageType.Float32:
        return round(struct.unpack(">f", buf.read(4))[0], 4)
    elif param_type == ReliableMessageType.Int32:
        return struct.unpack(">I", buf.read(4))[0]
    elif param_type in (ReliableMessageType.Int16, 7):
        return struct.unpack(">H", buf.read(2))[0]
    elif param_type == ReliableMessageType.Int64:
        return struct.unpack(">Q", buf.read(8))[0]
    elif param_type == ReliableMessageType.String:
        size = struct.unpack(">H", buf.read(2))[0]
        return buf.read(size).decode('utf-8', errors='ignore')
    elif param_type == ReliableMessageType.Boolean:
        return {0: False, 1: True}.get(buf.read(1)[0], False)
    elif param_type == ReliableMessageType.Int8Array:
        size = struct.unpack(">I", buf.read(4))[0]
        return list(buf.read(size))
    elif param_type == ReliableMessageType.StringArray:
        size = struct.unpack(">H", buf.read(2))[0]
        return [decode_type(buf, ReliableMessageType.String) for _ in range(size)]
    elif param_type == ReliableMessageType.Array:
        size, t = struct.unpack(">HB", buf.read(3))
        return [decode_type(buf, t) for _ in range(size)]
    elif param_type == ReliableMessageType.ObjectArray:
        size = struct.unpack(">H", buf.read(2))[0]
        # Object array elements are self-typed
        arr = []
        for _ in range(size):
            t = struct.unpack(">B", buf.read(1))[0]
            arr.append(decode_type(buf, t))
        return arr
    elif param_type == ReliableMessageType.Dictionary:
        keyTypeCode, valueTypeCode, dictionarySize = struct.unpack(">BBH", buf.read(4))
        dictionary = {}
        for _ in range(dictionarySize):
            key = decode_type(buf, keyTypeCode)
            value = decode_type(buf, valueTypeCode)
            dictionary[key] = value
        return dictionary
    elif param_type == ReliableMessageType.Hashtable:
        size = struct.unpack(">H", buf.read(2))[0]
        dictionary = {}
        for _ in range(size):
            k_type = struct.unpack(">B", buf.read(1))[0]
            key = decode_type(buf, k_type)
            v_type = struct.unpack(">B", buf.read(1))[0]
            value = decode_type(buf, v_type)
            dictionary[key] = value
        return dictionary

    return None

class ReliableMessage:
    def __init__(self, signature, msg_type, operation_code, parameters, debug_string=None, event_code=None):
        self.signature = signature
        self.type = msg_type
        self.operation_code = operation_code
        self.parameters = parameters
        self.debug_string = debug_string
        self.event_code = event_code

    @classmethod
    def unpack(cls, buf: io.BytesIO):
        # Header: Signature (1), Type (1)
        if len(buf.getbuffer()) < 2: return None
        signature, msg_type = struct.unpack(">BB", buf.read(2))
        
        operation_code = 0
        event_code = 0
        debug_string = None
        
        # Parse Type-Specific Header
        if msg_type == MessageType.OperationRequest:
            (operation_code,) = struct.unpack(">B", buf.read(1))
            
        elif msg_type == MessageType.EventData:
            (event_code,) = struct.unpack(">B", buf.read(1))
            
        elif msg_type in (MessageType.OperationResponse, MessageType.OtherOperationResponse):
            operation_code, operation_response_code, dbg_type = struct.unpack(">BHB", buf.read(4))
            # Handle Debug String
            if dbg_type != ReliableMessageType.Nil:
                debug_string = decode_type(buf, dbg_type)
        
        # Parameter Count
        if len(buf.getbuffer()) - buf.tell() < 2:
            return None # Malformed
            
        (param_count,) = struct.unpack(">H", buf.read(2))
        
        # Decode Parameters
        parameters = {}
        for _ in range(param_count):
            param_id = struct.unpack(">B", buf.read(1))[0]
            param_type = struct.unpack(">B", buf.read(1))[0]
            parameters[param_id] = decode_type(buf, param_type)
            
        return cls(
            signature=signature,
            msg_type=msg_type,
            operation_code=operation_code,
            parameters=parameters,
            debug_string=debug_string,
            event_code=event_code
        )