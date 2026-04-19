import io
import struct

from pydantic import BaseModel


class ReliableFragment(BaseModel):
    sequence_number: int
    fragment_count: int
    fragment_number: int
    total_length: int
    fragment_offset: int

    data: bytes

    @classmethod
    def unpack(cls, buf: io.BytesIO) -> "ReliableFragment":
        s = struct.Struct(">5i")
        (
            sequence_number,
            fragment_count,
            fragment_number,
            total_length,
            fragment_offset,
        ) = s.unpack(buf.read(s.size))

        return cls(
            sequence_number=sequence_number,
            fragment_count=fragment_count,
            fragment_number=fragment_number,
            total_length=total_length,
            fragment_offset=fragment_offset,
            data=buf.read(total_length),
        )
