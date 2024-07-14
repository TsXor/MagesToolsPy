from typing import Optional, Iterable
from pathlib import Path
import warnings
from dataclasses import dataclass
from mages_tools.errors import *
from mages_tools.io import *

@dataclass(slots=True)
class MPKLayout:
    HEADER = b'MPK\0'
    DEFAULT_MAGIC = 0x00020000
    ENTRY_SIZE = 256
    ENTRY_HEADER_SIZE = 32
    ENTRY_NAME_MAX_SIZE = ENTRY_SIZE - ENTRY_HEADER_SIZE
    ENTRY_DATA_ALIGN_UNIT = 0x800

    entries: dict[bytes, bytes]
    magic: int = DEFAULT_MAGIC
    entry_order: Optional[list[tuple[bytes, int]]] = None # 记录表的排列顺序，可忽略
    data_order: Optional[list[bytes]] = None # 记录数据的排列顺序，可忽略

    @classmethod
    def next_aligned(cls, addr: int):
        left = addr % cls.ENTRY_DATA_ALIGN_UNIT
        if left == 0: return addr
        return addr - left + cls.ENTRY_DATA_ALIGN_UNIT

    def entry_dump_order(self, follow_given: bool) -> Iterable[tuple[bytes, int]]:
        if follow_given and self.entry_order is not None and len(self.entry_order) == len(self.entries):
            return self.entry_order
        else: return zip(sorted(self.entries.keys()), range(len(self.entries)))

    def data_dump_order(self, follow_given: bool) -> Iterable[bytes]:
        if follow_given and self.data_order is not None and len(self.data_order) == len(self.entries):
            return self.data_order
        else: return sorted(self.entries.keys())

    @classmethod
    def load(cls, data: Readable):
        # 检查文件头
        if data.read(len(cls.HEADER)) != cls.HEADER:
            raise InvalidDataError("MPK header mismatch")
        # 读取魔数
        magic = data.read_u32()
        # 读取记录总数
        count = data.read_i32()
        if count <= 0: raise InvalidDataError("invalid entry count")
        data.read_until(0x40) # 跳过对齐
        # 读取记录表
        entry_order = list[tuple[bytes, int]]()
        entry_pos = list[tuple[int, int]]()
        for entry_idx in range(count):
            data.read_u32() # 跳过对齐
            marked_idx = data.read_u32()
            if entry_idx != marked_idx: warnings.warn("entry index mismatch", InformalDataWarning)
            offset = data.read_u64()
            if offset % cls.ENTRY_DATA_ALIGN_UNIT != 0: warnings.warn("entry data is not aligned", InformalDataWarning)
            size = data.read_u64(); also_size = data.read_u64()
            if size != also_size: warnings.warn("redundant entry size mismatch", InformalDataWarning)
            name = data.read_zstr()
            entry_order.append((name, marked_idx))
            entry_pos.append((offset, size))
            data.read(cls.ENTRY_NAME_MAX_SIZE - len(name) - 1)
        # 读取记录数据
        entry_index = sorted(range(len(entry_pos)), key=lambda i: entry_pos[i][0])
        entries = dict[bytes, bytes]()
        data_order = list[bytes]()
        for idx in entry_index:
            offset, size = entry_pos[idx]
            name, _ = entry_order[idx]
            data.read_until(offset)
            entries[name] = data.read(size)
            data_order.append(name)
        # 返回结果
        return cls(
            entries=entries,
            magic=magic,
            entry_order=entry_order,
            data_order=data_order,
        )

    def dump(self, data: Writable, follow_given_order: bool = False):
        # 写入文件头
        data.write(self.HEADER)
        # 写入魔数
        data.write_u32(self.magic)
        # 写入记录总数
        data.write_i32(len(self.entries))
        data.pad_until(0x40) # 对齐
        # 写入记录表
        entry_pos = dict[bytes, tuple[int, int]]()
        entry_offset = self.next_aligned(0x40 + self.ENTRY_SIZE * len(self.entries))
        for name in self.data_dump_order(follow_given_order):
            entry_data = self.entries[name]
            entry_pos[name] = (entry_offset, len(entry_data))
            entry_offset = self.next_aligned(entry_offset + len(entry_data))
        for name, marked_idx in self.entry_dump_order(follow_given_order):
            data.write_u32(0) # 对齐
            data.write_u32(marked_idx)
            offset, size = entry_pos[name]
            data.write_u64(offset)
            data.write_u64(size); data.write_u64(size)
            if len(name) + 1 > self.ENTRY_NAME_MAX_SIZE:
                raise InvalidDataError(f"entry name {repr(name)} too long")
            data.write_zstr(name)
            data.pad(self.ENTRY_NAME_MAX_SIZE - len(name) - 1)
        # 写入记录数据
        for name in self.data_dump_order(follow_given_order):
            offset, _ = entry_pos[name]
            data.pad_until(offset)
            data.write(self.entries[name])

    @classmethod
    def read(cls, path: str | Path):
        with open(path, 'rb') as fp:
            return cls.load(FileWrapper(fp))

    def write(self, path: str | Path):
        with open(path, 'wb') as fp:
            self.dump(FileWrapper(fp))
