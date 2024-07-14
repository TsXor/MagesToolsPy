from pathlib import Path
from .layout import MPKLayout, FileWrapper

def unpack(src: Path, dst: Path):
    if not (src.is_file() and dst.is_dir()):
        raise ValueError('invalid path')
    with open(src, 'rb') as fp:
        pkg = MPKLayout.load(FileWrapper(fp))
    basedir = dst / src.stem
    basedir.mkdir(exist_ok=True)
    for name, data in pkg.entries.items():
        (basedir / name.decode()).write_bytes(data)

def repack(src: Path, dst: Path):
    if not (src.is_dir() and dst.is_dir()):
        raise ValueError('invalid path')
    entries = dict[bytes, bytes]()
    for sub in src.iterdir():
        entries[sub.name.encode()] = sub.read_bytes()
    pkg = MPKLayout(entries=entries)
    filename = src.name + '.mpk'
    with open(dst / filename, 'wb') as fp:
        pkg.dump(FileWrapper(fp))
