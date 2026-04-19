from typing import Optional, Dict
from pydantic import BaseModel
from .base_photon_command import BasePhotonCommand
from .enums import CommandType
from .reliable_fragment import ReliableFragment

class FragmentBufferEntry(BaseModel):
    sequence_number: int
    fragments_needed: int
    fragments: Dict[int, bytes]

    def finished(self):
        return self.fragments_needed == len(self.fragments)

    def make(self) -> "BasePhotonCommand":
        data = b"".join(
            i[1] for i in sorted(self.fragments.items(), key=lambda x: x[0])
        )
        return BasePhotonCommand(
            type=CommandType.SendReliableType,
            data=data,
            reliable_sequence_number=self.sequence_number,
        )

class FragmentBuffer:
    def __init__(self):
        self.buf: Dict[int, FragmentBufferEntry] = {}

    def offer(self, msg: "ReliableFragment") -> Optional["BasePhotonCommand"]:
        if msg.sequence_number in self.buf:
            entry = self.buf[msg.sequence_number]
            entry.fragments[msg.fragment_number] = msg.data
        else:
            entry = FragmentBufferEntry(
                sequence_number=msg.sequence_number,
                fragments_needed=msg.fragment_count,
                fragments={},
            )
            entry.fragments[msg.fragment_number] = msg.data
            self.buf[msg.sequence_number] = entry

        if entry.finished():
            cmd = entry.make()
            del self.buf[msg.sequence_number]
            return cmd
        return None