from abc import ABC, abstractmethod
from typing import BinaryIO, ByteString
from io import SEEK_END

__all__ = [
    'Sequencial',
    'Seekable',
    'Readable',
    'Writable',
    'RandomReadable',
    'RandomWritable',
    'RandomAccessible',
    'ROBuffer',
    'FileWrapper',
]

class Sequencial(ABC):
    @abstractmethod
    def tell(self) -> int: pass

    @abstractmethod
    def size(self) -> int: pass

class Seekable(Sequencial):
    @abstractmethod
    def seek(self, pos: int) -> None: pass

    def move(self, offset: int): self.seek(self.tell() + offset)

class Readable(Sequencial):
    @abstractmethod
    def read(self, size: int) -> bytes: pass

    def read_u8(self):
        return int.from_bytes(self.read(1), byteorder='little', signed=False)

    def read_i8(self):
        return int.from_bytes(self.read(1), byteorder='little', signed=True)

    def read_u16(self):
        return int.from_bytes(self.read(2), byteorder='little', signed=False)

    def read_i16(self):
        return int.from_bytes(self.read(2), byteorder='little', signed=True)

    def read_u32(self):
        return int.from_bytes(self.read(4), byteorder='little', signed=False)

    def read_i32(self):
        return int.from_bytes(self.read(4), byteorder='little', signed=True)

    def read_u64(self):
        return int.from_bytes(self.read(8), byteorder='little', signed=False)

    def read_i64(self):
        return int.from_bytes(self.read(8), byteorder='little', signed=True)

    def read_charcode(self):
        return int.from_bytes(self.read(2), byteorder='big', signed=False) - 0x8000

    def read_until(self, pos: int): return self.read(pos - self.tell())

    def read_zstr(self):
        result = bytearray()
        while (ch := self.read(1)) != b'\0':
            result.extend(ch)
        return bytes(result)

class Writable(Sequencial):
    @abstractmethod
    def write(self, data: ByteString) -> None: pass

    def write_u8(self, val: int):
        self.write(val.to_bytes(1, byteorder='little', signed=False))

    def write_i8(self, val: int):
        self.write(val.to_bytes(1, byteorder='little', signed=True))

    def write_u16(self, val: int):
        self.write(val.to_bytes(2, byteorder='little', signed=False))

    def write_i16(self, val: int):
        self.write(val.to_bytes(2, byteorder='little', signed=True))

    def write_u32(self, val: int):
        self.write(val.to_bytes(4, byteorder='little', signed=False))

    def write_i32(self, val: int):
        self.write(val.to_bytes(4, byteorder='little', signed=True))

    def write_u64(self, val: int):
        self.write(val.to_bytes(8, byteorder='little', signed=False))

    def write_i64(self, val: int):
        self.write(val.to_bytes(8, byteorder='little', signed=True))

    def write_charcode(self, val: int):
        self.write((val + 0x8000).to_bytes(2, byteorder='big', signed=False))

    def pad(self, size: int, pattern: ByteString = b'\0'):
        for i in range(size // len(pattern)): self.write(pattern)
        self.write(pattern[:size % len(pattern)])

    def pad_until(self, pos: int, pattern: ByteString = b'\0'):
        self.pad(pos - self.tell(), pattern)

    def write_zstr(self, val: ByteString):
        self.write(val); self.write(b'\0')

class RandomReadable(Seekable, Readable): pass

class RandomWritable(Seekable, Writable): pass

class RandomAccessible(Seekable, Readable, Writable): pass

class ROBuffer(RandomReadable):
    buf: ByteString; pos: int

    def __init__(self, buf: ByteString):
        self.buf = buf; self.pos = 0

    def read(self, size: int):
        old_pos = self.pos; self.pos += size
        return self.buf[old_pos:self.pos]

    def seek(self, pos: int): self.pos = pos

    def tell(self): return self.pos

    def size(self): return len(self.buf)

class FileWrapper(RandomAccessible):
    fp: BinaryIO

    def __init__(self, fp: BinaryIO):
        self.fp = fp

    def tell(self): return self.fp.tell()

    def size(self):
        pos = self.fp.tell()
        self.fp.seek(0, SEEK_END)
        size = self.fp.tell()
        self.fp.seek(pos)
        return size

    def read(self, size: int): return self.fp.read(size)

    def write(self, data: ByteString): self.fp.write(data)

    def seek(self, pos: int): self.fp.seek(pos)
