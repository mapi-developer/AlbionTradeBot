import io
import struct

from pydantic import BaseModel

from photon_observer.base_photon_command import BasePhotonCommand
from photon_observer.enums import CommandType

sPhotonLayerHeader = struct.Struct(">HBBII")
sPhotonCommandHeader = struct.Struct(">BBBBII")
sReliableMessageHeader = struct.Struct(">BB")


class PhotonCommand(BasePhotonCommand):
    channel_id: int
    flags: int
    reserved_byte: int
    length: int

    @classmethod
    def unpack(cls, data: io.BytesIO) -> "PhotonCommand":
        (
            t,
            channel_id,
            flags,
            reserved_byte,
            length,
            reliable_sequence_number,
        ) = sPhotonCommandHeader.unpack(data.read(sPhotonCommandHeader.size))

        data_length = length - sPhotonCommandHeader.size

        return cls(
            type=t,
            channel_id=channel_id,
            flags=flags,
            reserved_byte=reserved_byte,
            length=length,
            reliable_sequence_number=reliable_sequence_number,
            data=data.read(data_length),
        )

    @property
    def size(self):
        return sPhotonCommandHeader.size + len(self.data)

    def unreliable_type(self):
        return PhotonCommand(
            type=CommandType.SendReliableType,
            length=self.length - 4,
            data=self.data[4:],
            channel_id=self.channel_id,
            flags=self.flags,
            reserved_byte=self.reserved_byte,
            reliable_sequence_number=self.reliable_sequence_number,
        )


class PhotonLayer(BaseModel):
    class Config:
        orm_mode = True

    peer_id: int
    crc_enabled: int
    command_count: int
    timestamp: int
    challenge: int

    commands: list[PhotonCommand]
    contents: bytes
    payload: bytes

    @classmethod
    def unpack(cls, buf: io.BytesIO) -> "PhotonLayer":
        size = sPhotonLayerHeader.size
        (
            peer_id,
            crc_enabled,
            command_count,
            timestamp,
            challenge,
        ) = sPhotonLayerHeader.unpack(buf.read(size))

        commands = []

        for i in range(command_count):
            obj = PhotonCommand.unpack(buf)
            commands.append(obj)

        return cls(
            peer_id=peer_id,
            crc_enabled=crc_enabled,
            command_count=command_count,
            timestamp=timestamp,
            challenge=challenge,
            commands=commands,
            contents=buf.read(),
            payload=buf.read(),
        )
