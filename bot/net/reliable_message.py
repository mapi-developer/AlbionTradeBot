import io
import struct
from typing import Optional, Union
from pydantic import BaseModel
from .enums import MessageType

# ==========================================
# PROTOCOL 18 DESERIALIZER UTILITIES
# ==========================================

def read_compressed_uint32(buf: io.BytesIO) -> int:
    value = 0
    shift = 0
    while True:
        b_bytes = buf.read(1)
        if not b_bytes:
            return 0
        b = b_bytes[0]
        value |= (b & 0x7F) << shift
        if (b & 0x80) == 0:
            return value
        shift += 7
        if shift >= 35:
            return 0

def read_compressed_uint64(buf: io.BytesIO) -> int:
    value = 0
    shift = 0
    while True:
        b_bytes = buf.read(1)
        if not b_bytes:
            return 0
        b = b_bytes[0]
        value |= (b & 0x7F) << shift
        if (b & 0x80) == 0:
            return value
        shift += 7
        if shift >= 70:
            return 0

def read_compressed_int32(buf: io.BytesIO) -> int:
    v = read_compressed_uint32(buf)
    return (v >> 1) ^ (-(v & 1))

def read_compressed_int64(buf: io.BytesIO) -> int:
    v = read_compressed_uint64(buf)
    return (v >> 1) ^ (-(v & 1))

def read_string(buf: io.BytesIO) -> str:
    length = read_compressed_uint32(buf)
    if length == 0:
        return ""
    return buf.read(length).decode('utf-8', errors='ignore')

def deserialize_custom_payload(buf: io.BytesIO, custom_id: int, is_slim: bool):
    size = read_compressed_uint32(buf)
    data = buf.read(size)
    return {"type": custom_id, "data": data}

def deserialize_custom(buf: io.BytesIO, gp_type: int):
    is_slim = gp_type >= 0x80
    if is_slim:
        custom_id = gp_type & 0x7F
    else:
        custom_id = buf.read(1)[0]
    return deserialize_custom_payload(buf, custom_id, is_slim)

def deserialize_parameter_table(buf: io.BytesIO):
    count = read_compressed_uint32(buf)
    params = {}
    for _ in range(count):
        k_bytes = buf.read(1)
        if not k_bytes: break
        tc_bytes = buf.read(1)
        if not tc_bytes: break
        params[k_bytes[0]] = decode_type(buf, tc_bytes[0])
    return params

def deserialize_typed_array(buf: io.BytesIO, elem_tc: int):
    size = read_compressed_uint32(buf)
    if elem_tc == 2:  # boolean array
        packed_bytes = (size + 7) // 8
        packed = buf.read(packed_bytes)
        result = []
        for i in range(size):
            result.append((packed[i // 8] & (1 << (i % 8))) != 0)
        return result
    elif elem_tc == 3:  # Byte array
        return list(buf.read(size))
    elif elem_tc == 4:  # Short array
        return [struct.unpack("<h", buf.read(2))[0] for _ in range(size)]
    elif elem_tc == 5:  # Float array
        return [struct.unpack("<f", buf.read(4))[0] for _ in range(size)]
    elif elem_tc == 6:  # Double array
        return [struct.unpack("<d", buf.read(8))[0] for _ in range(size)]
    elif elem_tc == 7:  # String array
        return [read_string(buf) for _ in range(size)]
    elif elem_tc == 9:  # CompressedInt array
        return [read_compressed_int32(buf) for _ in range(size)]
    elif elem_tc == 10: # CompressedLong array
        return [read_compressed_int64(buf) for _ in range(size)]
    elif elem_tc == 19: # Custom array
        custom_id = buf.read(1)[0]
        return [deserialize_custom_payload(buf, custom_id, False) for _ in range(size)]
    elif elem_tc in (20, 21): # Dict / Hashtable array
        return [decode_type(buf, elem_tc) for _ in range(size)]
    else:
        return [decode_type(buf, elem_tc) for _ in range(size)]

def decode_type(buf: io.BytesIO, tc: int):
    # Slim Custom Types
    if tc >= 0x80:
        return deserialize_custom(buf, tc)
    
    if tc == 0 or tc == 8: return None
    elif tc == 2: return buf.read(1)[0] != 0
    elif tc == 3: return buf.read(1)[0]
    elif tc == 4: return struct.unpack("<h", buf.read(2))[0]
    elif tc == 5: return round(struct.unpack("<f", buf.read(4))[0], 4)
    elif tc == 6: return struct.unpack("<d", buf.read(8))[0]
    elif tc == 7: return read_string(buf)
    elif tc == 9: return read_compressed_int32(buf)
    elif tc == 10: return read_compressed_int64(buf)
    elif tc == 11: return struct.unpack("<b", buf.read(1))[0]
    elif tc == 12: return -struct.unpack("<b", buf.read(1))[0]
    elif tc == 13: return struct.unpack("<H", buf.read(2))[0]
    elif tc == 14: return -struct.unpack("<H", buf.read(2))[0]
    elif tc == 15: return struct.unpack("<b", buf.read(1))[0]
    elif tc == 16: return -struct.unpack("<b", buf.read(1))[0]
    elif tc == 17: return struct.unpack("<H", buf.read(2))[0]
    elif tc == 18: return -struct.unpack("<H", buf.read(2))[0]
    elif tc == 19: return deserialize_custom(buf, 0)
    elif tc == 20 or tc == 21: # Dictionary / Hashtable
        key_tc = buf.read(1)[0]
        val_tc = buf.read(1)[0]
        count = read_compressed_uint32(buf)
        out = {}
        for _ in range(count):
            kt = buf.read(1)[0] if key_tc == 0 else key_tc
            vt = buf.read(1)[0] if val_tc == 0 else val_tc
            k = decode_type(buf, kt)
            v = decode_type(buf, vt)
            if isinstance(k, (list, dict)): k = str(k) # Hashable keys
            out[k] = v
        return out
    elif tc == 23: # ObjectArray
        size = read_compressed_uint32(buf)
        return [decode_type(buf, buf.read(1)[0]) for _ in range(size)]
    elif tc == 24: # OperationRequest
        op_code = buf.read(1)[0]
        params = deserialize_parameter_table(buf)
        return {"operationCode": op_code, "parameters": params}
    elif tc == 25: # OperationResponse
        op_code = buf.read(1)[0]
        ret_code = struct.unpack("<h", buf.read(2))[0]
        dbg_msg = ""
        if buf.tell() < len(buf.getbuffer()):
            dbg_tc = buf.read(1)[0]
            if dbg_tc == 7: dbg_msg = read_string(buf)
            elif dbg_tc != 8: dbg_msg = str(decode_type(buf, dbg_tc))
        params = deserialize_parameter_table(buf)
        return {"operationCode": op_code, "returnCode": ret_code, "debugMessage": dbg_msg, "parameters": params}
    elif tc == 26: # EventData
        event_code = buf.read(1)[0]
        params = deserialize_parameter_table(buf)
        return {"event_code": event_code, "parameters": params}
    elif tc == 27: return False
    elif tc == 28: return True
    elif tc in (29, 30, 31, 34): return 0
    elif tc in (32, 33): return 0.0
    elif tc == 0x40: # Bare Array
        size = read_compressed_uint32(buf)
        tc_elem = buf.read(1)[0]
        return [decode_type(buf, tc_elem) for _ in range(size)]
    elif tc & 0x40 == 0x40: # Typed Array
        return deserialize_typed_array(buf, tc & ~0x40)
    
    raise ValueError(f"Unknown type code: {tc}")

# ==========================================
# MESSAGE CLASSES
# ==========================================

class ReliableMessage(BaseModel):
    signature: int
    type: MessageType
    data: bytes

    @classmethod
    def unpack(cls, buf: io.BytesIO) -> Union["EventDataType", "OperationResponse", "OperationRequest", None]:
        if len(buf.getbuffer()) < 2: return None
        signature, t = struct.unpack(">BB", buf.read(2))
        
        try:
            t = MessageType(t)
            _cls = {
                MessageType.EventDataType: EventDataType,
                MessageType.OperationRequest: OperationRequest,
                MessageType.OperationResponse: OperationResponse,
                MessageType.otherOperationResponse: OperationResponse,
            }[t]
        except: return None

        # Protocol 18 parses parameters directly alongside the header data
        kwargs = _cls.read_data(buf)
        if kwargs is None: return None

        return _cls(
            signature=signature,
            type=t,
            **kwargs,
            data=buf.read(),
        )

    @classmethod
    def read_data(cls, buf: io.BytesIO):
        raise NotImplementedError()

    def decode(self):
        # Backward compatibility for your sniffer.py: 
        # Inject the operation code (253) and event code (252) into the parameters dictionary.
        params = getattr(self, "parameters", {}).copy()
        if hasattr(self, "operation_code"):
            params[253] = self.operation_code
        if hasattr(self, "event_code"):
            params[252] = self.event_code
        return params

class OperationRequest(ReliableMessage):
    operation_code: int
    parameters: dict
    @classmethod
    def read_data(cls, buf: io.BytesIO):
        op_code = buf.read(1)[0]
        params = deserialize_parameter_table(buf)
        return {"operation_code": op_code, "parameters": params}

class EventDataType(ReliableMessage):
    event_code: int
    parameters: dict
    @classmethod
    def read_data(cls, buf: io.BytesIO):
        event_code = buf.read(1)[0]
        params = deserialize_parameter_table(buf)
        return {"event_code": event_code, "parameters": params}

class OperationResponse(ReliableMessage):
    operation_code: int
    operation_response_code: int
    operation_debug_string: Optional[str] = None
    parameters: dict
    @classmethod
    def read_data(cls, buf: io.BytesIO):
        op_code = buf.read(1)[0]
        ret_code = struct.unpack("<h", buf.read(2))[0] # Little Endian!
        dbg_msg = ""
        dbg_tc = buf.read(1)[0]
        if dbg_tc == 7:
            dbg_msg = read_string(buf)
        elif dbg_tc != 8:
            dbg_msg = str(decode_type(buf, dbg_tc))
        params = deserialize_parameter_table(buf)
        return {
            "operation_code": op_code, 
            "operation_response_code": ret_code, 
            "operation_debug_string": dbg_msg, 
            "parameters": params
        }