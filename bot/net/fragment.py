import io
import struct

class ReliableFragment:
    def __init__(self, sequence_number, fragment_count, fragment_number, total_length, fragment_offset, data):
        self.sequence_number = sequence_number
        self.fragment_count = fragment_count
        self.fragment_number = fragment_number
        self.total_length = total_length
        self.fragment_offset = fragment_offset
        self.data = data

    @classmethod
    def unpack(cls, buf: io.BytesIO):
        # Header: Sequence(4), Count(4), Number(4), TotalLen(4), Offset(4)
        header_data = buf.read(20)
        if len(header_data) < 20:
            return None
            
        (
            sequence_number,
            fragment_count,
            fragment_number,
            total_length,
            fragment_offset,
        ) = struct.unpack(">iiiii", header_data)

        # Read the rest of the payload as the fragment data
        data = buf.read()

        return cls(
            sequence_number=sequence_number,
            fragment_count=fragment_count,
            fragment_number=fragment_number,
            total_length=total_length,
            fragment_offset=fragment_offset,
            data=data,
        )

class FragmentBufferEntry:
    def __init__(self, sequence_number, fragments_needed):
        self.sequence_number = sequence_number
        self.fragments_needed = fragments_needed
        self.fragments = {} # Dict[int, bytes]

    def finished(self):
        return self.fragments_needed == len(self.fragments)

    def make(self) -> bytes:
        # Sort by fragment number (key) to ensure correct order
        sorted_fragments = sorted(self.fragments.items(), key=lambda x: x[0])
        # Join the data bytes
        return b"".join(data for _, data in sorted_fragments)

class FragmentBuffer:
    def __init__(self):
        self.buffers = {} # Dict[int, FragmentBufferEntry]

    def offer(self, msg: ReliableFragment):
        if msg.sequence_number in self.buffers:
            entry = self.buffers[msg.sequence_number]
            entry.fragments[msg.fragment_number] = msg.data
        else:
            entry = FragmentBufferEntry(
                sequence_number=msg.sequence_number,
                fragments_needed=msg.fragment_count
            )
            entry.fragments[msg.fragment_number] = msg.data
            self.buffers[msg.sequence_number] = entry

        if entry.finished():
            # Reassembly complete
            data = entry.make()
            del self.buffers[msg.sequence_number]
            return data
        
        return None