import io
import struct
from . import constants as const

class PhotonDataDecoder:
    def __init__(self, stream):
        self.stream = stream if isinstance(stream, io.BytesIO) else io.BytesIO(stream)

    def decode(self):
        params = {}
        try:
            while True:
                if self.stream.tell() >= len(self.stream.getbuffer()):
                    break
                
                # Read Key (Byte) and Type (Byte)
                param_id_bytes = self.stream.read(1)
                if not param_id_bytes: break
                param_id = struct.unpack(">B", param_id_bytes)[0]
                
                param_type_bytes = self.stream.read(1)
                if not param_type_bytes: break
                param_type = struct.unpack(">B", param_type_bytes)[0]
                
                params[param_id] = self.decode_type(param_type)
        except Exception:
            pass
        return params

    def decode_type(self, type_id):
        s = self.stream
        if type_id == const.TYPE_NIL: return None
        elif type_id == const.TYPE_INT8: return struct.unpack(">b", s.read(1))[0]
        elif type_id == const.TYPE_INT16: return struct.unpack(">h", s.read(2))[0]
        elif type_id == const.TYPE_INT32: return struct.unpack(">i", s.read(4))[0]
        elif type_id == const.TYPE_INT64: return struct.unpack(">q", s.read(8))[0]
        elif type_id == const.TYPE_FLOAT32: return struct.unpack(">f", s.read(4))[0]
        elif type_id == const.TYPE_DOUBLE: return struct.unpack(">d", s.read(8))[0]
        elif type_id == const.TYPE_BOOLEAN: return s.read(1) != b'\x00'
        elif type_id == const.TYPE_STRING: return self._read_string()
        elif type_id == const.TYPE_DICTIONARY: return self._read_dictionary()
        elif type_id == const.TYPE_ARRAY: return self._read_array()
        elif type_id == const.TYPE_INT8_ARRAY: return self._read_byte_array()
        elif type_id == const.TYPE_OBJECT_ARRAY: return self._read_array()
        
        # --- NEW TYPES ADDED FOR MAIL HANDLING ---
        elif type_id == const.TYPE_STRING_ARRAY: return self._read_string_array()
        elif type_id == const.TYPE_HASHTABLE: return self._read_hashtable()
        
        return None

    def _read_string(self):
        length = struct.unpack(">H", self.stream.read(2))[0]
        return self.stream.read(length).decode('utf-8', errors='ignore')

    def _read_byte_array(self):
        length = struct.unpack(">I", self.stream.read(4))[0]
        return list(self.stream.read(length))

    def _read_array(self):
        length = struct.unpack(">H", self.stream.read(2))[0]
        type_id = struct.unpack(">B", self.stream.read(1))[0]
        return [self.decode_type(type_id) for _ in range(length)]

    def _read_string_array(self):
        length = struct.unpack(">H", self.stream.read(2))[0]
        return [self._read_string() for _ in range(length)]

    def _read_dictionary(self):
        key_type = struct.unpack(">B", self.stream.read(1))[0]
        value_type = struct.unpack(">B", self.stream.read(1))[0]
        size = struct.unpack(">H", self.stream.read(2))[0]
        data = {}
        for _ in range(size):
            key = self.decode_type(key_type)
            val = self.decode_type(value_type)
            data[key] = val
        return data

    def _read_hashtable(self):
        size = struct.unpack(">H", self.stream.read(2))[0]
        data = {}
        for _ in range(size):
            # Hashtable keys/values are self-typed
            key_type = struct.unpack(">B", self.stream.read(1))[0]
            key = self.decode_type(key_type)
            val_type = struct.unpack(">B", self.stream.read(1))[0]
            val = self.decode_type(val_type)
            data[key] = val
        return data