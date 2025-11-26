# photon/decoder.py
import io
import struct
from .constants import *

class PhotonDataDecoder:
    def __init__(self, stream):
        # We accept either bytes or an existing BytesIO stream
        if isinstance(stream, bytes):
            self.stream = io.BytesIO(stream)
        else:
            self.stream = stream

    def decode(self):
        """
        Reads the Dictionary of parameters usually found in the payload.
        Ref: DecodeReliableMessage in Go
        """
        params = {}
        try:
            # Keep reading (ParamID, ParamType, Value) until stream ends
            while True:
                # Peek to see if we have data left
                if self.stream.tell() >= len(self.stream.getbuffer()):
                    break
                
                param_id_bytes = self.stream.read(1)
                if not param_id_bytes: break
                param_id = struct.unpack(">B", param_id_bytes)[0]
                
                param_type_bytes = self.stream.read(1)
                if not param_type_bytes: break
                param_type = struct.unpack(">B", param_type_bytes)[0]
                
                params[param_id] = self.decode_type(param_type)
        except Exception as e:
            # print(f"Decoder Error: {e}")
            pass
            
        return params

    def decode_type(self, type_id):
        """
        Ref: decodeType in Go
        """
        if type_id == TYPE_NIL:
            return None
        
        elif type_id == TYPE_INT8:
            return struct.unpack(">b", self.stream.read(1))[0]
        
        elif type_id == TYPE_INT16:
            return struct.unpack(">h", self.stream.read(2))[0]
        
        elif type_id == TYPE_INT32:
            return struct.unpack(">i", self.stream.read(4))[0]
        
        elif type_id == TYPE_INT64:
            return struct.unpack(">q", self.stream.read(8))[0]
        
        elif type_id == TYPE_FLOAT32:
            return struct.unpack(">f", self.stream.read(4))[0]
        
        elif type_id == TYPE_DOUBLE:
            return struct.unpack(">d", self.stream.read(8))[0]
        
        elif type_id == TYPE_BOOLEAN:
            return self.stream.read(1) != b'\x00'
        
        elif type_id == TYPE_STRING:
            return self._read_string()
        
        elif type_id == TYPE_DICTIONARY:
            return self._read_dictionary()
        
        elif type_id == TYPE_ARRAY:
            return self._read_array()
            
        elif type_id == TYPE_INT8_ARRAY:
            return self._read_byte_array()
            
        else:
            # Fail-safe for unknown types to prevent crash, though data might be corrupt after this
            return f"Unknown<{type_id}>"

    def _read_string(self):
        # Length (2 bytes) + Bytes
        length = struct.unpack(">H", self.stream.read(2))[0]
        return self.stream.read(length).decode('utf-8', errors='ignore')

    def _read_byte_array(self):
        # Length (4 bytes) + Bytes
        length = struct.unpack(">I", self.stream.read(4))[0]
        return list(self.stream.read(length))

    def _read_array(self):
        # Length (2 bytes) + Type (1 byte) + Items
        length = struct.unpack(">H", self.stream.read(2))[0]
        type_id = struct.unpack(">B", self.stream.read(1))[0]
        
        arr = []
        for _ in range(length):
            arr.append(self.decode_type(type_id))
        return arr

    def _read_dictionary(self):
        # KeyType (1) + ValueType (1) + Size (2)
        key_type = struct.unpack(">B", self.stream.read(1))[0]
        value_type = struct.unpack(">B", self.stream.read(1))[0]
        size = struct.unpack(">H", self.stream.read(2))[0]
        
        data = {}
        for _ in range(size):
            key = self.decode_type(key_type)
            value = self.decode_type(value_type)
            data[key] = value
        return data