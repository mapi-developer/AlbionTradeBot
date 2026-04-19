import io
import struct
from typing import List
from pydantic import BaseModel
from .base_photon_command import BasePhotonCommand
from .enums import CommandType

sPhotonLayerHeader = struct.Struct(">HBBII")
sPhotonCommandHeader = struct.Struct(">BBBBII")

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

class PhotonLayer(BaseModel):
    peer_id: int
    crc_enabled: int
    command_count: int
    timestamp: int
    challenge: int
    commands: List[PhotonCommand]
    payload: bytes

    @classmethod
    def unpack(cls, buf: io.BytesIO) -> "PhotonLayer":
        if len(buf.getbuffer()) < sPhotonLayerHeader.size:
            return cls(peer_id=0, crc_enabled=0, command_count=0, timestamp=0, challenge=0, commands=[], payload=b"")

        (
            peer_id,
            crc_enabled,
            command_count,
            timestamp,
            challenge,
        ) = sPhotonLayerHeader.unpack(buf.read(sPhotonLayerHeader.size))

        commands = []
        try:
            for _ in range(command_count):
                if len(buf.getbuffer()) - buf.tell() < sPhotonCommandHeader.size: break
                obj = PhotonCommand.unpack(buf)
                commands.append(obj)
        except Exception: pass

        return cls(
            peer_id=peer_id,
            crc_enabled=crc_enabled,
            command_count=command_count,
            timestamp=timestamp,
            challenge=challenge,
            commands=commands,
            payload=buf.read(),
        )