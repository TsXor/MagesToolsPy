from typing import Optional, Iterable
from pathlib import Path
from array import array
from dataclasses import dataclass
from mages_tools.errors import *
from mages_tools.io import *

@dataclass(slots=True)
class SCXLayout:
    HEADER = b'SC3\0'

    entry_label: int
    labels: 'array[int]'
    codes_raw: bytes
    return_addrs: 'array[int]'
    strings_raw: list[bytes]
    string_order: Optional[list[int]] = None # 字符串数据的排列顺序，可忽略

    def string_dump_order(self, follow_given: bool) -> Iterable[int]:
        if follow_given and self.string_order is not None and len(self.string_order) == len(self.strings_raw):
            return self.string_order
        else: return range(len(self.strings_raw))

    @classmethod
    def load(cls, data: Readable):
        # 检查文件头
        if data.read(len(cls.HEADER)) != cls.HEADER:
            raise InvalidDataError("SCX header mismatch")
        # 读取表位置
        string_table_addr = data.read_u32()
        return_addr_table_addr = data.read_u32()
        # 读取标签表
        entry_label = data.read_u32()
        labels = array('L', [entry_label])
        labels.frombytes(data.read_until(entry_label))
        # 读取代码区
        code_data = data.read_until(string_table_addr)
        # 读取字符串表
        string_addrs = array('L', data.read_until(return_addr_table_addr))
        string_order = sorted(range(len(string_addrs)), key=lambda i: string_addrs[i])
        # 注：字符串表可能为空
        if string_addrs:
            # 读取返回地址表
            return_addrs = array('L', data.read_until(string_addrs[string_order[0]]))
            # 读取字符串数据
            string_data = [b''] * len(string_addrs)
            for cur, nxt in zip(string_order[:-1], string_order[1:]):
                string_data[cur] = data.read_until(string_addrs[nxt])
            string_data[string_order[-1]] = data.read_until(data.size())
        else:
            # 读取返回地址表
            return_addrs = array('L', data.read_until(data.size()))
            # 无字符串数据
            string_data = list[bytes]()
        # 返回结果
        return cls(
            entry_label=entry_label,
            labels=labels,
            codes_raw=code_data,
            return_addrs=return_addrs,
            strings_raw=string_data,
            string_order=string_order,
        )

    def dump(self, data: Writable, follow_given_order: bool = False):
        # 写入文件头
        data.write(self.HEADER)
        # 写入表位置
        string_table_addr = len(self.HEADER) + 4 * 2 + 4 * len(self.labels) + len(self.codes_raw)
        data.write_u32(string_table_addr)
        return_addr_table_addr = string_table_addr + 4 * len(self.strings_raw)
        data.write_u32(return_addr_table_addr)
        # 写入标签表
        data.write(self.labels.tobytes())
        # 写入代码区
        data.write(self.codes_raw)
        # 写入字符串表
        string_data_addr = return_addr_table_addr + 4 * len(self.return_addrs)
        string_addrs = array('L', [string_data_addr] * len(self.strings_raw))
        stroff = 0
        for stridx in self.string_dump_order(follow_given_order):
            string_addrs[stridx] += stroff
            stroff += len(self.strings_raw[stridx])
        data.write(string_addrs.tobytes())
        # 写入返回地址表
        data.write(self.return_addrs.tobytes())
        # 写入字符串数据
        for stridx in self.string_dump_order(follow_given_order):
            data.write(self.strings_raw[stridx])

    @classmethod
    def read(cls, path: str | Path):
        with open(path, 'rb') as fp:
            return cls.load(FileWrapper(fp))

    def write(self, path: str | Path):
        with open(path, 'wb') as fp:
            self.dump(FileWrapper(fp))
