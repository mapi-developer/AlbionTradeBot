from enum import Enum


class CommandType(int, Enum):
    AcknowledgeType = 1
    ConnectType = 2
    VerifyConnectType = 3
    DisconnectType = 4
    PingType = 5
    SendReliableType = 6
    SendUnreliableType = 7
    SendReliableFragmentType = 8

    def __repr__(self):
        return str(self.name)


class MessageType(int, Enum):
    OperationRequest = 2
    otherOperationResponse = 3
    EventDataType = 4
    OperationResponse = 7

    def __repr__(self):
        return str(self.name)


class ReliableMessageType(int, Enum):
    NilType = 42
    DictionaryType = 68
    StringSliceType = 97
    Int8Type = 98
    Custom = 99
    DoubleType = 100
    EventDateType = 101
    Float32Type = 102
    Hashtable = 104
    Int32Type = 105
    Int16Type = 107
    Int64Type = 108
    Int32SliceType = 110
    BooleanType = 111
    OperationResponseType = 112
    OperationRequestType = 113
    StringType = 115
    Int8SliceType = 120
    SliceType = 121
    ObjectSliceType = 122
