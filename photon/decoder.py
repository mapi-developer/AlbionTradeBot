import io
import struct
from .constants import *

class PhotonDataDecoder:
    def __init__(self, payload: bytes):
        self.stream = io.BytesIO(payload)

    def decode(self):
        """
        Decodes the payload into a Python dictionary.
        Ref: DecodeReliableMessage in decode_reliable_message.go
        """
        # The reliable message usually starts with a signature or count.
        # However, based on standard Photon, the payload of an OperationResponse 
        # is largely a Dictionary of Parameters.
        
        # NOTE: The Go code implies a specific header structure for reliable messages.
        # We will attempt to parse parameters directly assuming we are passed
        # the raw command payload after the header.
        
        params = {}
        # In Go: binary.Read(buf, ... &paramID); ... &paramType
        # We loop until the stream is exhausted.
        
        try:
            # Usually starts with parameters. 
            # If the payload is a serialized Dictionary (Type 68), we read it directly.
            # Otherwise we read id/type pairs.
            while self.stream.tell() < len(self.stream.getbuffer()):
                param_id_bytes = self.stream.read(1)
                if not param_id_bytes: break
                param_id = struct.unpack(">B", param_id_bytes)[0]
                
                param_type_bytes = self.stream.read(1)
                if not param_type_bytes: break
                param_type = struct.unpack(">B", param_type_bytes)[0]
                
                params[param_id] = self._decode_type(param_type)
                
        except Exception as e:
            # End of stream or malformed
            pass
            
        return params

    def _decode_type(self, type_id):
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
        elif type_id == TYPE_STRING_ARRAY:
            return self._read_array(TYPE_STRING)
        elif type_id == TYPE_INT8_ARRAY:
            return self._read_byte_array()
        else:
            # Fallback for types not strictly needed for Market Data
            return f"UnknownType<{type_id}>"

    def _read_string(self):
        # Go: binary.Read(buf, binary.BigEndian, &length) -> read bytes
        length = struct.unpack(">H", self.stream.read(2))[0]
        return self.stream.read(length).decode('utf-8', errors='ignore')

    def _read_byte_array(self):
        length = struct.unpack(">I", self.stream.read(4))[0]
        return list(self.stream.read(length))

    def _read_array(self, forced_type=None):
        length = struct.unpack(">H", self.stream.read(2))[0]
        type_id = forced_type
        
        if type_id is None:
            type_id = struct.unpack(">B", self.stream.read(1))[0]
            
        arr = []
        for _ in range(length):
            arr.append(self._decode_type(type_id))
        return arr

    def _read_dictionary(self):
        # Ref: decodeDictionaryType in decode_reliable_message.go
        key_type = struct.unpack(">B", self.stream.read(1))[0]
        value_type = struct.unpack(">B", self.stream.read(1))[0]
        size = struct.unpack(">H", self.stream.read(2))[0]
        
        data = {}
        for _ in range(size):
            key = self._decode_type(key_type)
            value = self._decode_type(value_type)
            data[key] = value
        return data