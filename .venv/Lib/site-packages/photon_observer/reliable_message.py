import io
import struct
from typing import Optional, Union

from pydantic import BaseModel

from .enums import MessageType, ReliableMessageType

sReliableMessageHeader = struct.Struct(">BB")


def decode_type(buf: io.BytesIO, param_type: ReliableMessageType):
    if param_type in (ReliableMessageType.NilType, 0):
        return None
    elif param_type == ReliableMessageType.Int8Type:
        return struct.unpack(">b", buf.read(1))[0]
    elif param_type == ReliableMessageType.Float32Type:
        return round(struct.unpack(">f", buf.read(4))[0], 4)
    elif param_type == ReliableMessageType.Int32Type:
        return struct.unpack(">I", buf.read(4))[0]
    elif param_type in (ReliableMessageType.Int16Type, 7):
        return struct.unpack(">H", buf.read(2))[0]
    elif param_type == ReliableMessageType.Int64Type:
        return struct.unpack(">Q", buf.read(8))[0]
    elif param_type == ReliableMessageType.StringType:
        size = struct.unpack(">H", buf.read(2))[0]
        return buf.read(size).decode()
    elif param_type == ReliableMessageType.BooleanType:
        return {0: False, 1: True}[buf.read(1)[0]]
    elif param_type == ReliableMessageType.Int8SliceType:
        size = struct.unpack(">I", buf.read(4))[0]
        array = []
        for i in range(size):
            array.append(struct.unpack(">B", buf.read(1))[0])
        return array
    elif param_type == ReliableMessageType.SliceType:
        size, t = struct.unpack(">HB", buf.read(3))
        array = []
        for i in range(size):
            array.append(decode_type(buf, t))
        return array
    elif param_type == ReliableMessageType.DictionaryType:
        keyTypeCode, valueTypeCode, dictionarySize = struct.unpack(">BBH", buf.read(4))
        dictionary = {}
        for i in range(dictionarySize):
            key = decode_type(buf, keyTypeCode)
            value = decode_type(buf, valueTypeCode)
            dictionary[key] = value
        return dictionary

    raise NotImplementedError(f"Unknown ReliableMessageType: {param_type}")


class ReliableMessage(BaseModel):
    signature: int
    type: MessageType

    paramater_count: int
    data: bytes

    @classmethod
    def unpack(
        cls, buf: io.BytesIO
    ) -> Union["EventDataType", "OperationResponse", "OperationRequest"]:
        signature, t = buf.read(sReliableMessageHeader.size)
        t = MessageType(t)

        _cls = {
            MessageType.EventDataType: EventDataType,
            MessageType.OperationRequest: OperationRequest,
            MessageType.OperationResponse: OperationResponse,
            MessageType.otherOperationResponse: OperationResponse,
        }[t]

        kwargs = _cls.read_data(buf)

        (paramater_count,) = struct.unpack(">H", buf.read(2))

        return _cls(
            signature=signature,
            type=t,
            **kwargs,
            paramater_count=paramater_count,
            data=buf.read(),
        )

    @classmethod
    def read_data(cls, buf: io.BytesIO):
        raise NotImplementedError()

    def decode(self):
        buf = io.BytesIO(self.data)
        params = {}

        for i in range(self.paramater_count):
            param_id, param_type = struct.unpack(">BB", buf.read(2))
            params[param_id] = decode_type(buf, param_type)

        return params


class OperationRequest(ReliableMessage):
    operation_code: int

    @classmethod
    def read_data(cls, buf: io.BytesIO):
        (operation_code,) = struct.unpack(">B", buf.read(1))
        return {"operation_code": operation_code}


class EventDataType(ReliableMessage):
    event_code: int

    @classmethod
    def read_data(cls, buf: io.BytesIO):
        (event_code,) = struct.unpack(">B", buf.read(1))
        return {"event_code": event_code}


class OperationResponse(ReliableMessage):
    operation_code: int
    operation_response_code: int

    operation_debug_string: Optional[str]

    @classmethod
    def read_data(cls, buf: io.BytesIO):
        operation_code, operation_response_code, param_type = struct.unpack(
            ">BHB", buf.read(4)
        )
        data = {
            "operation_code": operation_code,
            "operation_response_code": operation_response_code,
        }
        param_value = decode_type(buf, param_type)
        if param_value is not None:
            data["operation_debug_string"] = param_value

        return data
