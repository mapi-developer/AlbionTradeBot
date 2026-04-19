import io

from pydantic import BaseModel

from .enums import CommandType
from .reliable_fragment import ReliableFragment
from .reliable_message import ReliableMessage


class BasePhotonCommand(BaseModel):
    type: CommandType
    data: bytes
    reliable_sequence_number: int

    def reliable_message(self):
        return ReliableMessage.unpack(io.BytesIO(self.data))

    def reliable_fragment(self):
        return ReliableFragment.unpack(io.BytesIO(self.data))
